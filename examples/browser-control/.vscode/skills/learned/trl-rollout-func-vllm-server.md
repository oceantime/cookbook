# Skill: TRL rollout_func 接口与 vLLM Server 模式

**类别**: 机器学习 / TRL / vLLM  
**适用场景**: 自定义 GRPO rollout 逻辑（多步环境交互）  
**创建时间**: 2026-02-25

---

## 核心结论

### 1. `rollout_func` 在不同模式下的行为（版本相关）

> **重要：此行为与 TRL 版本相关，请以实际容器内版本为准。**

| 环境 | TRL 版本 | `vllm_mode="server"` | `vllm_mode="colocate"` |
|------|---------|----------------------|------------------------|
| 宿主机 .venv | 0.28.0（源码） | rollout_func 被调用 | rollout_func **不被调用**（`extra_fields = {}` 硬编码） |
| docker-training:latest 容器 | 实测更高版本 | rollout_func 被调用 | rollout_func **确实被调用**（签名为 2 参数：`prompts, trainer`） |

**结论**：不能依赖宿主机源码来判断容器内行为，**必须在容器内实际验证**。

#### `vllm_mode="server"` 下的调用（稳定）

```python
# trl/trainer/grpo_trainer.py:1179（宿主机 TRL 0.28.0 参考）
if self.vllm_mode == "server":
    if self.rollout_func is not None:
        output = self.rollout_func(ordered_set_of_prompts, self.args, self.processing_class)
    else:
        output = self.vllm_client.generate(...)  # 默认路径
```

#### `vllm_mode="colocate"` 下的情况（版本依赖）

```python
# 宿主机 TRL 0.28.0：rollout_func 永远不会被调用
elif self.vllm_mode == "colocate":
    all_outputs = self.llm.generate(all_prompts, ...)
    # extra_fields = {}  ← 硬编码，rollout_func 返回的 reward 丢失

# 容器内更高版本：rollout_func 会被调用（2参数签名）
# def rollout_func(prompts, trainer): ...
```

### 2. `RolloutFunc` 类型签名（精确）

```python
# trl/trainer/grpo_trainer.py:113
RolloutFunc = Callable[[list[str], Any, Any], dict[str, Any]]
#                        ^^^^^^^^   ^^^   ^^^^^^^^^^^^^^^^
#                        prompts    args  processing_class
```

**正确签名**：
```python
def my_rollout_func(
    prompts: list[str],        # 已经过 chat template 的文本（不是 tokenized）
    args,                      # GRPOConfig 实例
    processing_class,          # tokenizer
) -> dict[str, Any]:
    ...
```

**错误签名（不要这样写）**：
```python
# ❌ 错误：trainer 不是第二个参数，且 trainer.generate() 不存在
def my_rollout_func(prompts, trainer):
    completion = trainer.generate(...)  # AttributeError!
```

### 3. `rollout_func` 返回值格式

```python
{
    "prompt_ids":     list[list[int]],   # 必须
    "completion_ids": list[list[int]],   # 必须
    "logprobs":       list[list[float]], # 必须
    # 任意额外字段会被转发给 reward_func
}
```

### 4. 向 GRPOTrainer 注册 rollout_func

```python
# TRL 在内部调用前会先把 conversational prompts 展平为字符串
# 所以 rollout_func 收到的 prompts 是 list[str]（已完成 chat template）

trainer = GRPOTrainer(
    model=config.model_name,
    reward_funcs=[],
    train_dataset=dataset,
    processing_class=tokenizer,
    args=grpo_config,
    rollout_func=lambda prompts, args, processing_class: my_rollout(
        prompts=prompts,
        args=args,
        processing_class=processing_class,
        browsergym_url=browsergym_url,
        system_prompt=config.system_prompt,
    ),
)
```

---

## vLLM Server 模式配置

### YAML 配置

```yaml
use_vllm: true
vllm_mode: "server"          # 必须是 server，不能是 colocate
vllm_server_host: "0.0.0.0"
vllm_server_port: 9001       # 避免与 BrowserGym 的 8000 冲突
```

### GRPOConfig 对应字段

```python
grpo_config = GRPOConfig(
    use_vllm=True,
    vllm_mode="server",
    vllm_server_base_url="http://localhost:9001",  # 优先级高于 host+port
    # 或者：
    vllm_server_host="0.0.0.0",
    vllm_server_port=9001,
    vllm_server_timeout=240.0,
)
```

### 启动 vLLM Server（`trl vllm-serve`）

TRL 提供了内置命令启动与 GRPO trainer 兼容的 vLLM server：

```bash
python3.12 -m trl vllm-serve \
    --model LiquidAI/LFM2-350M \
    --port 9001 \
    --gpu-memory-utilization 0.5 \
    --cache-dir /hf_model_cache
```

在训练脚本中用子进程启动：

```python
import subprocess, time, requests

def start_vllm_server(model_name: str, port: int, cache_dir: str) -> subprocess.Popen:
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "trl", "vllm-serve",
            "--model", model_name,
            "--port", str(port),
            "--gpu-memory-utilization", "0.5",
        ],
        env={**os.environ, "HF_HOME": cache_dir},
    )
    # 等待 server 就绪
    base_url = f"http://localhost:{port}"
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/health/", timeout=2).status_code == 200:
                print(f"vLLM server ready at {base_url}")
                return proc
        except Exception:
            pass
        time.sleep(5)
    proc.terminate()
    raise RuntimeError(f"vLLM server failed to start on port {port}")
```

---

## VLLMClient 生成接口

```python
from trl.extras.vllm_client import VLLMClient

client = VLLMClient(base_url="http://localhost:9001", connection_timeout=240)

output = client.generate(
    prompts=["Hello, world!"],
    n=1,
    temperature=1.0,
    max_tokens=128,
)
# output: {
#   "prompt_ids":     [[101, 7592, ...]],     # list[list[int]]
#   "completion_ids": [[1234, 5678, ...]],    # list[list[int]]
#   "logprobs":       [[-0.5, -1.2, ...]],   # list[list[float]]
# }
```

---

## 完整 rollout_func 示例（多步 BrowserGym 交互）

```python
from trl.extras.vllm_client import VLLMClient

def rollout_func(
    prompts: list[str],      # TRL 传入：已 chat-template 化的文本
    args,                    # GRPOConfig
    processing_class,        # tokenizer（可用于 decode）
    browsergym_url: str,
    max_steps: int = 3,
) -> dict:
    vllm_client = VLLMClient(
        base_url=args.vllm_server_base_url or f"http://localhost:{args.vllm_server_port}",
        connection_timeout=240,
    )
    gym_client = BrowserGymHTTPClient(base_url=browsergym_url)

    all_prompt_ids, all_completion_ids, all_logprobs, all_rewards = [], [], [], []

    for prompt_text in prompts:
        prompt_ids = processing_class.encode(prompt_text, add_special_tokens=False)

        # reset 环境
        reset_resp = gym_client.reset()
        session_id = reset_resp["session_id"]

        done = False
        step = 0
        reward = 0.0
        completion_ids: list[int] = []
        logprobs: list[float] = []

        # 多步交互循环
        current_prompt = prompt_text
        try:
            while not done and step < max_steps:
                gen = vllm_client.generate(
                    prompts=[current_prompt],
                    n=1,
                    temperature=1.0,
                    max_tokens=args.max_completion_length,
                )
                completion_ids = gen["completion_ids"][0]
                logprobs = gen["logprobs"][0]
                action_text = processing_class.decode(completion_ids, skip_special_tokens=True).strip()

                step_resp = gym_client.step(session_id=session_id, action_str=action_text)
                obs_text = step_resp.get("observation", {}).get("text", "")
                reward = float(step_resp.get("reward") or 0.0)
                done = bool(step_resp.get("done", False))

                # 追加观察到 prompt（多轮对话）
                current_prompt += action_text + "\n" + obs_text
                step += 1
        finally:
            gym_client.close(session_id)

        all_prompt_ids.append(prompt_ids)
        all_completion_ids.append(completion_ids)
        all_logprobs.append(logprobs)
        all_rewards.append(reward)

    return {
        "prompt_ids":     all_prompt_ids,
        "completion_ids": all_completion_ids,
        "logprobs":       all_logprobs,
        "reward":         all_rewards,
    }
```

---

## rollout_func → reward_func 数据流（extra_fields 接线）

### 机制

`rollout_func` 返回值中，`prompt_ids`/`completion_ids`/`logprobs` 以外的所有键，会被 TRL 作为 `extra_fields` 透传给 `reward_func` 的 `**kwargs`。

```
rollout_func 返回:
{
  "prompt_ids":     [...],   # TRL 内部使用
  "completion_ids": [...],   # TRL 内部使用
  "logprobs":       [...],   # TRL 内部使用
  "reward":         [1.0],   # → extra_fields → reward_func(**kwargs)["reward"]
}
```

### reward_func 必须从 kwargs 读取 reward

```python
def browsergym_reward_func(
    prompts,
    completions,
    completion_ids=None,
    **kwargs
):
    rewards = kwargs.get("reward", None)
    if rewards is None:
        return [None] * len(prompts)
    return [float(r) for r in rewards]
```

### 常见陷阱

```python
# ❌ reward_funcs=[] —— rollout_func 返回的 reward 被忽略，GRPO 记录 reward=0.0
trainer = GRPOTrainer(
    reward_funcs=[],
    ...
)

# ✅ 必须提供 reward_func 从 kwargs 读取 reward
trainer = GRPOTrainer(
    reward_funcs=[browsergym_reward_func],
    ...
)
```

### 验证方式

训练日志中确认 reward 不为 0：
```
{'loss': 0.0821, 'grad_norm': 1.234, 'reward': 0.5, ...}
```

---

## 常见错误

| 错误 | 原因 | 修复 |
|------|------|------|
| `AttributeError: 'GRPOTrainer' object has no attribute 'generate'` | 调用了不存在的 `trainer.generate()` | 改用 `VLLMClient.generate()` |
| `rollout_func` 从未被调用（宿主机 TRL 0.28.0） | 使用了 `vllm_mode="colocate"` | 改为 `vllm_mode="server"` |
| `TypeError: <lambda>() takes 2 positional arguments but 3 were given` | rollout_func lambda 参数数量错误 | 签名改为 `(prompts, args, processing_class)` |
| vLLM server 连接超时 | server 未启动或端口冲突 | 检查端口，确保训练前 server 已就绪 |
| GRPO `reward=0.0`，loss=0 | `reward_funcs=[]` | 提供 `browsergym_reward_func` 读取 kwargs |

---

## 参考来源

- TRL 源码 `trl/trainer/grpo_trainer.py:113`（RolloutFunc 类型定义）
- TRL 源码 `trl/trainer/grpo_trainer.py:1179`（rollout_func 调用位置）
- TRL 源码 `trl/extras/vllm_client.py:181`（VLLMClient.generate 接口）
- TRL 源码 `trl/scripts/vllm_serve.py`（vllm-serve 命令实现）
- 实验验证：run20~run23（本地 Docker，DGX SPARK B10，2026-02-26）
