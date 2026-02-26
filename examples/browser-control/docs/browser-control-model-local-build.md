# 本地 GPU 构建 Browser Control 模型（DGX / 自有 GPU 服务器）

本文档描述如何在本地 GPU 服务器（如 NVIDIA DGX）上通过 Docker 构建训练环境并运行 GRPO 微调。

## 前置条件

- NVIDIA GPU（建议 A100 80GB 或同等规格）
- Docker + NVIDIA Container Toolkit
- `docker compose` v2

## 目录结构

```
docker/
├── training/        # 训练镜像 Dockerfile
├── browsergym/      # BrowserGym 环境镜像 Dockerfile
├── miniwob/         # MiniWoB++ 任务镜像 Dockerfile
└── logs/            # TensorBoard 日志（不提交）
```

## 构建步骤

### 1. 克隆 OpenEnv

```bash
cd docker/training
git clone https://github.com/meta-pytorch/OpenEnv.git
cd docker/browsergym
git clone https://github.com/meta-pytorch/OpenEnv.git
```

### 2. 构建镜像

```bash
docker compose -f docker/docker-compose.training.yml build
```

### 3. 启动 BrowserGym 服务

```bash
docker compose -f docker/docker-compose.training.yml up browsergym -d
```

### 4. 运行训练

```bash
docker compose -f docker/docker-compose.training.yml run training \
  python -m src.browser_control.fine_tune_local \
  --config-file-name lfm2_350m_local.yaml
```

### 5. 查看 TensorBoard

```bash
tensorboard --logdir docker/logs/
```

## 本地配置文件

| 文件 | 说明 |
|------|------|
| `configs/lfm2_350m_local.yaml` | 本地 GPU 全量微调 |
| `configs/lfm2_350m_local_full.yaml` | 本地 GPU 全量微调（大 batch） |
| `configs/lfm2_350m_local_lora.yaml` | 本地 GPU LoRA 微调 |

## 注意事项

- `docker/logs/` 由 Docker 容器（root 用户）写入，**不要提交到 git**
- `docker/*/OpenEnv/` 是克隆的外部仓库，**不要提交到 git**
- 权重保存至 `checkpoints/`，**不要提交到 git**
- `wandb_enabled: false` 可关闭 WandB 追踪（离线模式）
