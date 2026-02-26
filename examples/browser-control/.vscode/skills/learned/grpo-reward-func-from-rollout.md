# Skill: GRPO reward_func 与 rollout_func 的数据流接线

**类别**: 机器学习 / TRL / GRPO  
**适用场景**: 自定义环境交互的 GRPO 训练，reward 由 rollout_func 计算  
**创建时间**: 2026-02-26  
**验证环境**: DGX SPARK B10，docker-training:latest，BrowserGym HTTP REST

---

## 核心问题

使用自定义 `rollout_func` 与环境交互时（如 BrowserGym），reward 是在 rollout 阶段由环境返回的。如何让 TRL GRPO 真正使用这个 reward 更新模型？

---

## 数据流路径

```
rollout_func(prompts, ...)
    ↓ 与环境交互，获得 reward
    ↓ 返回 {"prompt_ids": ..., "completion_ids": ..., "logprobs": ..., "reward": [1.0, 0.0, ...]}
          ↑ 除前三个字段外，其余键→ extra_fields
TRL GRPOTrainer
    ↓ extra_fields 透传给 reward_func(**kwargs)
reward_func(prompts, completions, **kwargs)
    ↓ kwargs["reward"] = [1.0, 0.0, ...]
    ↓ return [1.0, 0.0, ...]
GRPO 优化
    ↓ 使用 reward 计算优势函数，更新模型参数
```

---

## 完整接线代码

### Step 1：rollout_func 返回 reward

```python
def rollout_func(prompts, args, processing_class, browsergym_url, max_steps=3):
    all_prompt_ids, all_completion_ids, all_logprobs, all_rewards = [], [], [], []

    for prompt_text in prompts:
        # ... 与 BrowserGym 交互 ...
        reward = float(step_resp.get("reward") or 0.0)

        all_rewards.append(reward)

    return {
        "prompt_ids":     all_prompt_ids,      # TRL 内部使用
        "completion_ids": all_completion_ids,  # TRL 内部使用
        "logprobs":       all_logprobs,        # TRL 内部使用
        "reward":         all_rewards,         # → extra_fields → reward_func(**kwargs)
    }
```

### Step 2：reward_func 从 kwargs 读取 reward

```python
def browsergym_reward_func(
    prompts: list[str],
    completions: list[str],
    completion_ids=None,
    **kwargs,
) -> list[float | None]:
    """从 rollout_func 的 extra_fields 中读取 reward。"""
    rewards = kwargs.get("reward", None)
    if rewards is None:
        # rollout_func 没有返回 reward 字段时的兜底
        return [None] * len(prompts)
    return [float(r) for r in rewards]
```

### Step 3：注册到 GRPOTrainer

```python
trainer = GRPOTrainer(
    model=config.model_name,
    reward_funcs=[browsergym_reward_func],   # ← 必须提供，不能是 []
    train_dataset=dataset,
    processing_class=tokenizer,
    args=grpo_config,
    rollout_func=lambda prompts, args, processing_class: rollout_func(
        prompts=prompts,
        args=args,
        processing_class=processing_class,
        browsergym_url=browsergym_url,
    ),
)
```

---

## 常见错误及对比

### ❌ 错误：reward_funcs=[]

```python
trainer = GRPOTrainer(reward_funcs=[], ...)
```

**结果**：
- rollout_func 中 reward=1.0 被正确计算
- 但 TRL 没有 reward_func 读取它
- GRPO 记录 `reward=0.0`，`loss=0.0`
- 模型参数不更新，训练白跑

### ✅ 正确：提供读取 kwargs 的 reward_func

```python
trainer = GRPOTrainer(reward_funcs=[browsergym_reward_func], ...)
```

**结果**：
- `reward=0.5`（本例中50%成功率）
- `loss` 非零，`grad_norm` 正常
- 模型正常学习

---

## 验证训练是否正常工作

训练日志中观察以下指标：

```
# 正常训练（reward 不为 0，loss 非零）
{'loss': 0.0821, 'grad_norm': 1.234, 'reward': 0.5, 'reward_std': 0.5, ...}

# 异常（reward=0，loss=0，模型未学习）
{'loss': 0.0, 'grad_norm': 0.0, 'reward': 0.0, 'reward_std': 0.0, ...}
```

---

## 多 reward_func 叠加

TRL 支持多个 reward_func，最终 reward 是加权求和：

```python
trainer = GRPOTrainer(
    reward_funcs=[
        browsergym_reward_func,   # 来自环境的 reward
        format_reward_func,       # 格式奖励（如严格单行输出）
    ],
    reward_weights=[1.0, 0.1],    # 可选权重
    ...
)
```

---

## 参考

- 实验验证：run20（reward=0）→ run23（reward=0.5）对比，2026-02-26
- TRL 源码：`trl/trainer/grpo_trainer.py`（extra_fields 透传逻辑）
- 关联技能：`trl-rollout-func-vllm-server.md`（rollout_func 完整接口）
