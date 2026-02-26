# GRPO 训练配置与运行

## 背景
GRPO（Group Relative Policy Optimization）是一种适合语言模型的强化学习算法，通过组内相对奖励来优化策略，比 PPO 更稳定、内存效率更高。

## 核心参数

```yaml
# GRPO 相关参数
num_generations: 4          # 每个 prompt 生成的候选答案数（组大小）
generation_batch_size: 4    # 生成 batch 大小（须整除 num_generations）
per_device_train_batch_size: 1  # 训练时每设备 batch 大小
max_completion_length: 32   # 生成的最大 token 数
max_steps: 10               # 每次 rollout 的最大交互步数
learning_rate: 5.0e-6       # 学习率（全量微调）
warmup_steps: 10            # 线性 warmup 步数
```

## vLLM 加速
```yaml
use_vllm: true
vllm_mode: "colocate"       # 与训练共用同一 GPU
vllm_gpu_memory_utilization: 0.1  # 分配给 vLLM 的显存比例
```

## 奖励函数
BrowserGym 提供稀疏奖励：
- 任务完成 → reward = 1.0
- 未完成 → reward = 0.0
- 超时/错误 → reward = -0.1

## 监控训练
```bash
# WandB（云端）
# 访问 https://wandb.ai/<your-project>

# TensorBoard（本地）
tensorboard --logdir docker/logs/ --port 6006
```

## 常见调参建议
- 如果 reward 始终为 0：降低任务难度，先用 MiniWoB++ 简单任务验证
- 如果训练不稳定：增大 `num_generations`（4 → 8），降低 `learning_rate`
- 如果显存不足：启用 LoRA（`use_peft: true`），降低 `vllm_gpu_memory_utilization`
