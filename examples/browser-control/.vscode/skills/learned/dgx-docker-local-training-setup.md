# DGX 本地 Docker 训练环境构建

## 背景
本技能记录了在 NVIDIA DGX 服务器（或其他本地 GPU 机器）上，使用 Docker 构建 BrowserGym + GRPO 训练环境的完整流程，以及遇到的问题和解决方案。

## 环境信息
- 硬件：DGX A100（80GB × 8）
- OS：Ubuntu 22.04
- Docker：24.x + NVIDIA Container Toolkit
- 训练框架：TRL (GRPOTrainer) + vLLM

## 成功验证的配置

### STAGE 1：基础环境验证
- Docker 镜像构建成功（`docker/training/Dockerfile`）
- BrowserGym 服务启动成功（`docker/browsergym/Dockerfile`）
- 模型加载成功（LFM2-350M from HuggingFace）
- 单步 rollout 验证通过

### STAGE 2：完整训练运行
- GRPO 训练 10 steps 完成
- TensorBoard 日志写入 `docker/logs/`
- 权重保存至 `checkpoints/`

## Docker Compose 配置要点

```yaml
# docker-compose.training.yml 关键设置
services:
  training:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    volumes:
      - ./logs:/workspace/logs      # TensorBoard 日志
      - ./checkpoints:/workspace/checkpoints
    environment:
      - HF_HOME=/hf_cache
      - WANDB_API_KEY=${WANDB_API_KEY}

  browsergym:
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
```

## 已知问题

### docker/logs/ root 权限问题
**问题**：Docker 容器以 root 用户写入 `docker/logs/`，导致 host 用户无法删除，git 操作报权限错误。

**解决方案**：
1. 将 `docker/logs/` 加入 `.gitignore`
2. 如需清理：`sudo rm -rf docker/logs/*`
3. 或在 Dockerfile 中添加 `USER` 指令切换到非 root 用户

### vLLM colocate 模式显存分配
**问题**：`vllm_gpu_memory_utilization: 0.1` 时 OOM。

**解决**：使用 LoRA 配置（`lfm2_350m_local_lora.yaml`），降低全参数量。

## 训练配置建议（DGX A100 80GB）

| 参数 | 全量微调 | LoRA 微调 |
|------|---------|---------|
| `vllm_gpu_memory_utilization` | 0.3 | 0.15 |
| `per_device_train_batch_size` | 2 | 4 |
| `num_generations` | 8 | 8 |
| `max_completion_length` | 64 | 64 |

## 重要提醒
- `docker/logs/`、`docker/*/OpenEnv/`、`checkpoints/`、`llama.cpp/` 均已加入 `.gitignore`
- 推送前务必检查 `git status`，确认没有 root 权限文件被 `git add`
