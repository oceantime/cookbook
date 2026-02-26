# Skill: DGX SPARK B10 + Docker 本地训练环境搭建

**类别**: 基础设施 / Docker  
**适用场景**: 在 DGX SPARK B10（NVIDIA GB10）上搭建本地 Docker GRPO 训练环境  
**创建时间**: 2026-02-26  
**来源**: STAGE1_VERIFICATION_RESULT.md + STAGE2_PROGRESS.md

---

## 1. 硬件配置（已验证）

| 组件 | 规格 |
|------|------|
| GPU 型号 | NVIDIA GB10（Blackwell 架构） |
| 计算能力 | 12.1 |
| CUDA 驱动 | 580.126.09（CUDA 13.4） |
| Docker Engine | 29.1.3 |
| Docker Compose | v5.0.1 |
| 磁盘可用 | 3358 GB |

### 显存查询（nvidia-smi 显示 [N/A] 时）

```python
import torch
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Total Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
```

> GB10 上 `nvidia-smi` 显存列可能显示 `[N/A]`，这是新硬件驱动限制，不影响使用。

---

## 2. 环境验证步骤

```bash
# 1. 确认架构和驱动
uname -m          # aarch64
nvidia-smi        # 驱动 ≥ 530，CUDA 13.x

# 2. 确认 Docker
docker --version             # ≥ 20.10
docker compose version       # ≥ 2.0

# 3. 验证 NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:13.0.0-base-ubuntu22.04 nvidia-smi

# 4. 运行项目验证脚本
bash docker/scripts/verify_dgx.sh
```

---

## 3. Docker Compose 服务架构

```
docker/docker-compose.training.yml
├── browsergym      # BrowserGym 环境容器（端口 8000）
├── training        # GPU 训练容器（GRPO + vLLM colocate）
└── tensorboard     # 可视化容器（端口 6006，profile: monitoring）
```

### 网络与卷

```yaml
networks:
  training-net:     # bridge 网络，服务间通过服务名互访

volumes:
  hf_cache:         # HuggingFace 模型缓存
  checkpoints:      # 训练 checkpoint 存储
```

### 训练容器依赖栈

| 组件 | 版本 |
|------|------|
| 基础镜像 | `nvidia/cuda:13.0.0-devel-ubuntu22.04` |
| Python | 3.12（deadsnakes PPA） |
| uv 包管理器 | 最新 |
| PyTorch | 2.10.1 + CUDA 13.0 |
| trl[vllm] | ≥ 0.25.1 |
| transformers | ≥ 4.57.3 |
| peft | ≥ 0.13.0 |
| OpenEnv | git source |
| TensorBoard | 最新 |

### BrowserGym 容器依赖栈

| 组件 | 说明 |
|------|------|
| 基础镜像 | `python:3.11-slim` |
| Chromium + Xvfb + x11vnc | 无头浏览器环境 |
| BrowserGym + MiniWoB++ | 从 GitHub 克隆 |
| Playwright | chromium（手动安装依赖，见 `playwright-debian` 技能） |
| FastAPI server | `docker/browsergym/server.py` |

### BrowserGym FastAPI 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/` | 服务信息 |
| GET | `/status` | 服务状态 |
| POST | `/reset` | 开始新 episode |
| POST | `/step` | 执行动作 |
| POST | `/close` | 关闭 session |

---

## 4. GB10 推荐配置

```yaml
# docker-compose.training.yml
environment:
  - NVIDIA_VISIBLE_DEVICES=0
  - CUDA_VISIBLE_DEVICES=0

# configs/lfm2_350m_local.yaml
use_vllm: true
vllm_mode: "colocate"          # GB10 必须用 colocate，不支持 server 模式 NCCL
vllm_gpu_memory_utilization: 0.10   # 保守初始值
```

> **为什么必须用 colocate**：GB10 计算能力 12.1 超出 PyTorch 支持范围（8.0–12.0），`vllm_mode="server"` 会触发 NCCL `init_communicator` 永久挂起。详见 `trl-rollout` 技能。

---

## 5. Makefile 目标速查

| 命令 | 说明 |
|------|------|
| `make docker-build` | 构建所有 Docker 镜像 |
| `make fine-tune-local` | 启动调试训练（debug config） |
| `make fine-tune-local-full` | 启动完整训练（full config） |
| `make tensorboard` | 启动 TensorBoard（主机原生，http://localhost:6006） |
| `make checkpoint-download NAME=xxx` | 从 Docker volume 下载 checkpoint |
| `make docker-down` | 停止并清理所有容器 |
| `make docker-logs` | 查看训练日志 |
| `make docker-status` | 查看容器状态 |

### 镜像构建耗时参考

| 镜像 | 大小 | 耗时 |
|------|------|------|
| training | 15.4 GB | 10–15 分钟 |
| browsergym | 2.62 GB | 3–5 分钟 |

---

## 6. 关联技能

- `/skills arm64` — ARM64 + CUDA 13 PyTorch 配置
- `/skills playwright-debian` — BrowserGym Dockerfile Debian Trixie 字体包兼容性
- `/skills trl-rollout` — vllm_mode colocate vs server，GB10 NCCL 挂起根因
- `/skills checkpoint` — Docker Volume checkpoint 提取方案
