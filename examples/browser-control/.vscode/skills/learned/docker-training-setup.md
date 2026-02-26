# Docker 训练环境配置

## 目录结构

```
docker/
├── training/
│   ├── Dockerfile          # 训练镜像
│   └── OpenEnv/            # 克隆的 OpenEnv 仓库（不提交）
├── browsergym/
│   ├── Dockerfile          # BrowserGym 服务镜像
│   └── OpenEnv/            # 克隆的 OpenEnv 仓库（不提交）
├── miniwob/
│   └── Dockerfile          # MiniWoB++ 镜像（可选）
├── scripts/
│   └── entrypoint.sh       # 容器启动脚本
├── docker-compose.training.yml
└── logs/                   # TensorBoard 日志（不提交，root 权限）
```

## 训练镜像 (docker/training/Dockerfile)

```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

RUN apt-get update && apt-get install -y git python3 python3-pip curl
RUN pip install uv

WORKDIR /workspace
COPY OpenEnv/ /workspace/OpenEnv/
COPY ../../pyproject.toml ../../uv.lock ./
RUN uv sync

ENV HF_HOME=/hf_cache
ENV PYTHONPATH=/workspace
```

## BrowserGym 镜像 (docker/browsergym/Dockerfile)

```dockerfile
FROM python:3.12-slim

RUN pip install uv
WORKDIR /workspace
COPY OpenEnv/ /workspace/OpenEnv/
RUN cd OpenEnv && uv pip install -e ".[server]"

EXPOSE 8080
CMD ["python", "-m", "openenv.server", "--port", "8080"]
```

## docker-compose.training.yml 关键部分

```yaml
version: '3.8'
services:
  browsergym:
    build: ./browsergym
    ports: ["8080:8080"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      retries: 5

  training:
    build: ./training
    depends_on:
      browsergym:
        condition: service_healthy
    environment:
      - BROWSERGYM_URL=http://browsergym:8080
      - HF_TOKEN=${HF_TOKEN}
      - WANDB_API_KEY=${WANDB_API_KEY}
    volumes:
      - ./logs:/workspace/logs
      - ../checkpoints:/workspace/checkpoints
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

## 常用命令

```bash
# 构建所有镜像
docker compose -f docker/docker-compose.training.yml build

# 启动 BrowserGym（后台）
docker compose -f docker/docker-compose.training.yml up browsergym -d

# 运行训练
docker compose -f docker/docker-compose.training.yml run training \
  python -m src.browser_control.fine_tune_local \
  --config-file-name lfm2_350m_local_lora.yaml

# 查看日志
docker compose -f docker/docker-compose.training.yml logs -f

# 清理
docker compose -f docker/docker-compose.training.yml down
```
