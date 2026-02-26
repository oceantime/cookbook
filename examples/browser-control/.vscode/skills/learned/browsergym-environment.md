# Skill: BrowserGym 强化学习环境

**类别**: 强化学习 / 网页自动化  
**适用场景**: 基于 BrowserGym 训练网页操作 Agent  
**创建时间**: 2026-02-22  
**最后更新**: 2026-02-26（本地 Docker 构建，HTTP REST 模式验证）

---

## 架构

```
Agent（模型）
    ↓ 动作
BrowserGym 环境
    ├── BrowserEnv（Playwright）
    │   └── 真实浏览器实例
    ├── 任务定义（MiniWoB）
    │   └── 目标、初始状态、奖励函数
    └── 观察空间
        ├── DOM 树（完整 HTML）
        └── AXTree（可访问性树，压缩）
```

### 本地 Docker 构建架构（HTTP REST 模式）

```
training 容器
    └── rollout_func
            ↓ POST /reset
            ↓ POST /step
            ↓ POST /close
browsergym 容器（HTTP REST 服务，端口 8000）
    └── BrowserGymEnv（Playwright + MiniWoB）
```

---

## HTTP REST 接口（本地 Docker 模式）

### `/reset` — 开始新 episode

```python
POST http://browsergym:8000/reset
Body: {"task_name": "miniwob.click-test"}

Response:
{
  "session_id": "abc123",
  "observation": {
    "text": "",                   # 通常为空，不要依赖此字段
    "axtree_txt": "[13] button 'Click Me!'  ...",  # 主要观察内容
    "goal": "Click the button",
    "url": "http://localhost:8080/...",
    "screenshot": "<base64>",
    "pruned_html": "<html>...",
    "last_action_error": False,
    "error": None
  }
}
```

### `/step` — 执行一步动作

```python
POST http://browsergym:8000/step
Body: {"session_id": "abc123", "action": "click('13')"}

Response:
{
  "observation": { ... },  # 同上
  "reward": 1.0,           # 0.0 或 1.0（二元）
  "done": true,
  "truncated": false
}
```

### `/close` — 关闭 session

```python
POST http://browsergym:8000/close
Body: {"session_id": "abc123"}
```

### 关键注意事项

- `text` 字段**通常为空**，必须用 `axtree_txt`
- `last_action_error` 为 `True` 表示上一步 action 解析或执行失败
- session_id 必须在 `/close` 前保持有效，否则资源泄漏
- 并发 session 数有上限（`MAX_CONCURRENT_SESSIONS`），需在 rollout_func 中及时关闭

---

## 观察类型对比

| 类型 | 内容 | Token 数 | 速度 | 推荐 |
|------|------|---------|------|------|
| DOM 树 | 完整 HTML 结构 | 1000-5000 | 慢 | 调试 |
| AXTree | 仅语义结构 | 200-500 | 快 | 训练 ✅ |

---

## 动作空间（HighLevelActionSet）

BrowserGym 使用 `HighLevelActionSet`，action **必须是 Python 函数调用字符串**。

### 正确格式

```python
"click('13')"        # ✅ bid 必须是字符串（加引号）
"fill('5', 'hello')" # ✅
"press('Enter')"     # ✅
```

### 错误格式（常见坑）

```python
"click(13)"          # ❌ bid 是整数，解析失败
"click 13"           # ❌ 不是函数调用格式
"I will click on 13" # ❌ 自然语言，解析失败
```

### 从 AXTree 提取 bid

```
# axtree 示例
[13] button 'Click Me!'
 ↑
 bid = "13"（字符串）

# 对应 action
click('13')
```

### 常用 action 列表

```python
click('13')            # 点击元素
fill('5', 'John Doe')  # 向输入框填写文本
press('Enter')         # 键盘按键
scroll(0, 100)         # 滚动页面
```

### 传给模型的 system_prompt 要点

```
- 只输出单个 action，不要有其他文字
- bid 必须加引号：click('13') 而不是 click(13)
- 参考 axtree 中 [bid] 格式识别元素
```

---

## 观察字段完整说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `axtree_txt` | str | 主要观察内容，语义化 DOM 树 |
| `goal` | str | 任务目标描述 |
| `text` | str | 通常为空，不要使用 |
| `url` | str | 当前页面 URL |
| `screenshot` | str | base64 编码截图 |
| `pruned_html` | str | 裁剪后的 HTML |
| `last_action_error` | bool | 上一步 action 是否执行失败 |
| `error` | str\|None | 具体错误信息 |

### 构建传给模型的观察消息

```python
# 必须同时包含 goal 和 axtree_txt
observation_text = obs["axtree_txt"] or obs["text"]
obs_message = f"Goal: {goal}\n\nPage observation:\n{observation_text}"
```

---

## 奖励函数

- 二元奖励: 1.0（成功）或 0.0（失败）
- 稀疏奖励: 仅在 episode 结束时给出
- 任务特定: 每个 MiniWoB 任务有独立定义

---

## 错误处理

### SessionCapacityError（并发 session 超限）

```python
# 在 rollout_func 中用 try/finally 确保关闭
try:
    resp = requests.post(f"{url}/reset", json={"task_name": task})
    session_id = resp.json()["session_id"]
    # ... rollout 逻辑 ...
finally:
    requests.post(f"{url}/close", json={"session_id": session_id})
```

### last_action_error 处理

```python
step_resp = requests.post(f"{url}/step", json={"session_id": sid, "action": action})
obs = step_resp.json()["observation"]
if obs.get("last_action_error"):
    print(f"Action failed: {obs.get('error')}")
    # 可选：给 0 reward 或直接终止 episode
```

---

## HuggingFace Space 连接问题处理

```python
# HF Space 长时间不活跃可能进入休眠
try:
    env = BrowserGymEnv(...)
except ConnectionError:
    print("Waiting for HF Space to wake up...")
    time.sleep(30)
    env = BrowserGymEnv(...)  # 重试
```

---

## 构建信息

- **本地 Docker 模式**: HTTP REST（推荐用于 DGX/本地 GPU 环境）
- **HuggingFace Space**: `burtenshaw-browsergym-v2`（远程，无需本地 Playwright）

## 参考

- GitHub: https://github.com/ServiceNow/BrowserGym
- 论文: "BrowserGym: A Gym for Web Task Automation"
