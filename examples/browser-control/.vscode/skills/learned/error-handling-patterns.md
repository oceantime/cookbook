# 错误处理模式

## BrowserGym 连接错误

### 症状
```
ConnectionRefusedError: [Errno 111] Connection refused
requests.exceptions.ConnectionError: Failed to establish connection to http://localhost:8080
```

### 解决
1. 确认 BrowserGym 服务已启动：`docker compose ps`
2. 等待服务健康检查通过：`curl http://localhost:8080/health`
3. 检查 `browsergym_url` 配置是否正确

## vLLM OOM 错误

### 症状
```
torch.cuda.OutOfMemoryError: CUDA out of memory
RuntimeError: CUDA error: device-side assert triggered
```

### 解决
1. 降低 `vllm_gpu_memory_utilization`（如 0.1 → 0.05）
2. 减小 `per_device_train_batch_size`（改为 1）
3. 减小 `generation_batch_size`（改为 2）
4. 使用 LoRA 而非全量微调
5. 启用 `gradient_checkpointing: true`

## WandB 认证失败

### 症状
```
wandb: ERROR Failed to log in. Please set WANDB_API_KEY
```

### 解决
```bash
# Modal 构建
modal secret create wandb-secret WANDB_API_KEY=<your-key>

# 本地构建
echo "WANDB_API_KEY=<your-key>" >> .env
# 或关闭 WandB：
# wandb_enabled: false
```

## Docker root 权限文件冲突

### 症状
```
error: open("docker/logs/events.out.tfevents..."): Permission denied
```

### 解决
将 `docker/logs/` 加入 `.gitignore`：
```
docker/logs/
```
不要尝试 `git rm` 这些文件，会因权限报错。

## GRPO 训练不收敛

### 症状
- reward 始终为 0 或波动极大
- loss 不下降

### 解决
1. 检查 BrowserGym 任务是否太难（先用 miniwob++ 验证）
2. 增大 `num_generations`（从 4 → 8）
3. 降低 `learning_rate`（从 5e-6 → 1e-6）
4. 增加 `warmup_steps`（从 10 → 50）
5. 检查 `system_prompt` 是否清晰描述了动作格式
