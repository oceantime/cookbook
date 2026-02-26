# BrowserGym 环境配置与使用

## 背景
BrowserGym 是一个 OpenAI Gym 风格的浏览器控制环境，通过 HTTP API 提供网页交互任务。本项目使用 OpenEnv 版本的 BrowserGym。

## 环境类型
- **远程服务**（云端构建）：`browsergym_url: https://burtenshaw-browsergym-v2.hf.space`
- **本地 Docker**（本地构建）：`browsergym_url: http://localhost:8080`
- **MiniWoB++**：轻量级 web 任务集，适合快速验证

## 动作空间
```
noop()                    # 不操作
click(bid)                # 点击元素（bid 为 BrowserGym ID）
fill(bid, text)           # 填写输入框
send_keys(text)           # 键盘输入
scroll(direction)         # 滚动页面（up/down）
```

## 状态空间
环境返回 DOM 结构，格式为：
```
[bid] element_type 'element_text'
[13] button 'Submit'
[42] input '' (placeholder: 'Enter email')
```

## 本地 Docker 启动
```bash
# 构建并启动 BrowserGym 服务
docker compose -f docker/docker-compose.training.yml up browsergym -d

# 检查服务健康
curl http://localhost:8080/health
```

## 注意事项
- `dataset_size` 控制每次训练使用的任务数量（100 个适合快速迭代）
- BrowserGym 服务需要在训练启动前完全就绪
- 本地模式下 URL 为 `http://browsergym:8080`（Docker 网络内部名称）
