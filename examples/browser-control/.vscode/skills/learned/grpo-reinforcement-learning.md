# Skill: GRPO 强化学习

**类别**: 机器学习 / 强化学习  
**适用场景**: 使用 GRPO 微调语言模型  
**创建时间**: 2026-02-22

---

## 核心原理

**组相对策略优化（Group Relative Policy Optimization）**

- **基于组的优势**: 在小批次内比较响应
- **无价值网络**: 比 PPO 更节省内存
- **相对奖励**: 优于平均的响应获得正优势

## 实现

```python
from trl import GRPOConfig, GRPOTrainer

config = GRPOConfig(
    learning_rate=1e-6,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    # ... 其他超参数
)

trainer = GRPOTrainer(
    model=model,
    config=config,
    processing_class=tokenizer,
    reward_model=reward_model,
)
```

## 相比 PPO 的优势

- 更低的内存占用（无评论家/价值网络）
- 更简单的实现
- 更适合语言模型微调

## 调试配置（快速验证）

```yaml
# configs/lfm2_350m_debug.yaml
num_mini_batches: 2      # 减少批次大小
num_ppo_epochs: 1        # 单个 epoch
total_episodes: 10       # 少量 episode
max_new_tokens: 64       # 短响应
```

**调试工作流**:
1. 使用调试配置测试（A100 上 <3 分钟）
2. 监控 WandB 进行合理性检查
3. 下载检查点并验证
4. 扩展到完整配置

## 性能基准（LFM2-350M，A100）

| 模式 | 步数 | 耗时 |
|------|------|------|
| 调试 | 10 步 | ~2.5 分钟 |
| 完整微调 | 100 步 | ~25 分钟 |
| LoRA 微调 | 100 步 | ~8 分钟 |

## rollout_func 接口（自定义生成逻辑）

**重要**：`rollout_func` **只在 `vllm_mode="server"` 下被调用**，colocate 模式完全跳过它。

```python
# 正确签名（来自 TRL 源码第113行）
# RolloutFunc = Callable[[list[str], Any, Any], dict[str, Any]]

def my_rollout_func(
    prompts: list[str],   # 已过 chat template 的文本（非 tokenized）
    args,                 # GRPOConfig 实例
    processing_class,     # tokenizer
) -> dict:
    return {
        "prompt_ids":     [...],  # list[list[int]]，必须
        "completion_ids": [...],  # list[list[int]]，必须
        "logprobs":       [...],  # list[list[float]]，必须
        # 额外字段会被转发给 reward_func
    }

# 注册到 GRPOTrainer（lambda 必须有3个参数）
trainer = GRPOTrainer(
    ...
    rollout_func=lambda prompts, args, proc_cls: my_rollout_func(
        prompts, args, proc_cls, extra_param=value
    ),
)
```

详细文档见 `.vscode/skills/learned/trl-rollout-func-vllm-server.md`

## 参考资料

- TRL 文档: https://huggingface.co/docs/trl/grpo
- 论文: "Group Relative Policy Optimization"
- rollout_func 详解: `.vscode/skills/learned/trl-rollout-func-vllm-server.md`
