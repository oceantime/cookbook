# browser-control 本地Docker构建指南

> **最后更新**: 2026-02-26  
> **目标**: 将Modal云端训练迁移到完全本地Docker环境  
> **硬件平台**: DGX SPARK B10 (可适配其他NVIDIA GPU服务器)  
> **当前进度**: 阶段八：✅ 全部完成（run31 GGUF 转换完成，Q8_0/Q5_K_M/Q4_K_M/FP16 四种量化，llama-cli 验证通过）

## 1. 项目概述

基于 Liquid AI 的 cookbook 示例，将原有依赖 **Modal SaaS** 和 **HuggingFace Space** 的训练流程，迁移到基于 **Docker Compose** 的完全本地化架构，实现离线GRPO训练能力。

### 核心技术栈
- **模型**: LFM2-350M (Liquid AI)
- **RL 算法**: GRPO (Group Relative Policy Optimization)
- **环境**: BrowserGym (本地Docker容器)
- **推理**: vLLM (colocate模式，与训练共享 GPU 进程，TRL 内部管理)
- **基础设施**: Docker Compose + NVIDIA Container Toolkit
- **微调**: 支持 Full Fine-tune 和 LoRA
- **实验跟踪**: TensorBoard (本地) / MLflow (可选)

### 架构对比

| 组件 | Modal版本 | Docker本地版 |
|------|----------|-------------|
| GPU基础设施 | Modal A100 (按秒计费) | 本地GPU (DGX SPARK B10) |
| BrowserGym环境 | HF Space (远程) | Docker容器 (本地) |
| 存储卷 | Modal Volume | Docker Volume |
| 实验跟踪 | WandB (云端) | TensorBoard (本地) |
| 网络依赖 | 必需 | 可离线 |
| 数据隐私 | 上传云端 | 完全本地 |

---

## 2. 环境要求

### 2.1 硬件要求
| 组件 | 最低要求 | 推荐配置 | DGX SPARK B10 |
|------|---------|---------|---------------|
| GPU | NVIDIA GPU (CUDA 13.0+) | A100 40GB | ✅ NVIDIA GB10 (Compute 12.1) |
| GPU显存 | ≥ 24GB (RTX 4090) | ≥ 40GB (A100) | ✅ 已验证 |
| 系统内存 | ≥ 32GB | ≥ 64GB | ✅ 已验证 |
| 磁盘空间 | ≥ 100GB | ≥ 500GB (SSD) | ✅ 3358GB可用 |
| CUDA驱动 | ≥ 530 (CUDA 13.0) | 最新稳定版 | ✅ 580.126.09 |

### 2.2 软件依赖
| 组件 | 版本要求 | 验证命令 |
|------|---------|---------|
| Docker Engine | ≥ 20.10 | `docker --version` |
| Docker Compose | ≥ 2.0 | `docker compose version` |
| NVIDIA Driver | ≥ 530 | `nvidia-smi` |
| NVIDIA Container Toolkit | 最新 | `docker run --rm --gpus all nvidia/cuda:13.0.0-base nvidia-smi` |

### 2.3 核心依赖 (容器内自动安装)
```
Python 3.12
torch == 2.10.1 (CUDA 13.0)
trl >= 0.25.1 (GRPO + vLLM)
transformers >= 4.57.3
peft >= 0.13.0 (LoRA)
openenv (git source)
tensorboard (实验跟踪)
```

---

## 3. 构建任务清单

### 阶段一：环境准备 (5-10分钟) ✅ 已完成
- [x] 验证DGX GPU配置: `cd docker && bash scripts/verify_dgx.sh`
  - ✅ GPU: NVIDIA GB10, Compute Capability 12.1
  - ✅ 驱动: 580.126.09 (CUDA 13.4)
- [x] 确认NVIDIA驱动版本 ≥ 530
- [x] 安装Docker Engine (已安装 29.1.3)
- [x] 安装NVIDIA Container Toolkit (已验证可用)
- [x] 验证GPU Docker访问: `docker run --rm --gpus all nvidia/cuda:13.0.0-base nvidia-smi`
- [x] 克隆项目代码: `git clone <repo> && cd examples/browser-control`

### 阶段二：Docker镜像构建 (15-20分钟) ✅ 已完成
- [x] 创建Docker配置文件 (Dockerfile, docker-compose.yml)
- [x] 构建训练容器镜像: `docker compose build training`
  - ✅ 镜像大小: 15.4GB (包含PyTorch 2.10.0 + CUDA 13.0 + OpenEnv)
- [x] 优化BrowserGym容器Dockerfile
  - ✅ 解决Debian Trixie字体包兼容性问题
  - ✅ 修复Playwright安装参数
- [x] 构建BrowserGym容器镜像: `docker compose build browsergym`
  - ✅ 镜像大小: 2.62GB (创建于 2026-02-25 08:08)

### 阶段三：BrowserGym环境测试 ✅ 已完成
- [x] 单独启动BrowserGym: `docker-compose -f docker/docker-compose.training.yml up -d browsergym`
- [x] 等待健康检查通过 (约30秒)
- [x] 验证API可用: `curl http://localhost:8000/health` ✅
- [x] HTTP session API 端到端 curl 测试全部通过:
  - `POST /reset` → `{observation, session_id}` ✅
  - `POST /step` (带 session_id) → `{observation, reward, done}` ✅
  - `POST /close` (带 session_id) → `{ok: true}` ✅
  - `GET /health` ✅

### 阶段四：调试训练执行 ✅ 已完成

- [x] run13–run17：定位并修复多个基础问题
  - `trl.extras.vllm_client` → `trl.generation.vllm_client`（TRL 0.28 路径变更）
  - `python -m trl` → `trl` CLI（无 `__main__` 入口）
  - vLLM server 加 `HF_HUB_OFFLINE=1` 防止联网
  - `vllm_server_host` 改 `localhost`
- [x] run18：成功到达 `[INFO] Server is up!`，但卡死在 NCCL `init_communicator`
  - **根因**: TRL 0.28 `vllm_mode="server"` 强制调用 `init_communicator()`，通过 `StatelessProcessGroup.create()` 建立 NCCL TCP store 握手
  - PyTorch 明确不支持 NVIDIA GB10（Compute Capability 12.1，超出 PyTorch 的 8.0–12.0 范围）
  - **修复**: 改用 `vllm_mode="colocate"`，不调用 `init_communicator`
- [x] run19：改用 colocate 模式后 NCCL 挂起彻底解决
  - 模型加载 ✅，flashinfer 自调优 ✅，CUDA graphs 捕获（100%）✅
  - 训练流程进入第一次 rollout，但 BrowserGym `/reset` 返回 500
  - **根因**：多次 `/close` 后 Playwright event loop 被销毁，下次 `/reset` 无法建立新 session
  - **修复方向**：持久化 session（不调 `/close`），rollout 之间复用同一 session_id
- [x] run20：实现持久 session 策略，管道跑通（exit 0）
  - `/reset` 500 彻底解决 ✅
  - **发现**：模型输出 action 格式错误（`click(13)` 而非 `click('13')`），`last_action_error=True`
  - **发现**：`reward_funcs=[]` 导致 GRPO `reward=0.0`，模型未学习
- [x] run21：加详细调试日志，确认 obs/action/reward 数据流
  - 验证 `text` 字段为空，正确字段是 `axtree_txt`
  - 确认 bid 必须是字符串格式（`click('13')` 而非 `click(13)`）
- [x] run22：强化 `system_prompt`（bid 格式示例），修复 obs 包含 goal 一起传模型
  - `reward=1.0` 开始出现，action 格式正确 ✅
  - GRPO `reward` 仍=0（`reward_funcs=[]` 未修复）
- [x] run23：新增 `browsergym_reward_func`，注册到 `reward_funcs`
  - ✅ GRPO `reward=0.5`，`loss` 非零，`grad_norm` 正常
  - ✅ 端到端训练管道完全验证通过
- [x] 观察 GRPO loss/reward 输出 ✅（run23 验证）
- [x] 验证 checkpoint 生成 ✅

### 阶段五：TensorBoard监控 ✅ 已完成
- [x] 启动TensorBoard: `make tensorboard`
  - ✅ ARM64 不兼容 `tensorflow/tensorflow:latest`（x86_64 镜像，QEMU SIGSEGV 崩溃）
  - ✅ 改用主机原生 TensorBoard：`/home/tony/.local/bin/tensorboard`
  - ✅ Makefile `make tensorboard` 已更新为调用主机原生命令
- [x] 浏览器访问: http://localhost:6006 ✅
- [x] 验证训练曲线显示（run27，34个 step-level scalar 标签）✅
- [x] `fine_tune_local.py` 中 `report_to` 始终为 `"tensorboard"`（不受 `wandb_enabled` 控制）✅

### 阶段六：检查点管理 ✅ 已完成
- [x] 查看Docker Volume内容: `docker volume inspect browser-control-checkpoints` ✅
- [x] 清理旧检查点（105.8GB → 21.2GB），只保留 run27 ✅
  - 保留: `LFM2-350M-browsergym-20260226-023155`（run27，调试验证基准）
- [x] 验证检查点大小约21.2GB（safetensors格式，Full Fine-tune）✅

### 阶段七：完整训练 ✅ 已完成
- [x] run30：LR=5e-6，100步，step 21 entropy崩溃死锁（reward_std=0 → advantage=0 → 无梯度）
  - 根因：单一任务（click-test），模型学会后所有 rollout reward=1.0，reward_std=0
  - step 20 grad_norm=10.7 灾难性更新 → step 21 entropy=0.04 → 永久死锁
  - 已在 step 52 手动停止
- [x] 降低 `learning_rate: 5e-6 → 1e-6`（`configs/lfm2_350m_local_full.yaml`）
- [x] run31：LR=1e-6，100步，**训练成功完成** ✅
  - `train_loss=-0.007`，总耗时 31 分钟
  - entropy 在 step 36 保持 2.16（run30 同步为 0.007，相差约 300 倍）
  - 检查点: `LFM2-350M-browsergym-20260226-031516`（21.2G）
- [x] 清理旧检查点和 TensorBoard 日志，只保留 run27 + run31 ✅
  - 检查点 volume：42.4G（原 75G）
  - TensorBoard 日志：2个目录（原 6个）

### 阶段八：GGUF 模型转换 ✅ 已完成
- [x] 确认 llama.cpp 二进制完整（`llama-quantize`, `llama-cli` 均存在于 `llama.cpp/build/bin/`）
- [x] 从 Docker volume 将 run31 检查点复制到宿主机 `checkpoints/LFM2-350M-browsergym-20260226-031516/`
- [x] 修改 `scripts/convert_to_gguf_local.py` 的 checkpoint 路径指向 run31
- [x] 执行转换，生成以下 GGUF 文件（`gguf_models_local/`）：
  - `lfm2-350m-browsergym-fp16.gguf`：678.52 MB
  - `lfm2-350m-browsergym-q8_0.gguf`：361.65 MB（生产推荐）
  - `lfm2-350m-browsergym-q5_k_m.gguf`：248.31 MB
  - `lfm2-350m-browsergym-q4_k_m.gguf`：218.69 MB
  - 量化耗时：Q8_0=698ms, Q5_K_M=1.7s, Q4_K_M=1.9s
- [x] `llama-cli` 验证 Q8_0 模型正常推理（模型加载成功，15.2 t/s CPU 模式）✅

---

### 4.0 历次 run 错误记录

| run | 结果 | 错误/发现 | 修复 |
|-----|------|----------|------|
| run14 | ❌ | `ModuleNotFoundError: trl.extras.vllm_client` | 改为 `trl.generation.vllm_client` |
| run15 | ❌ | `No module named trl.__main__` | 改用 `trl` CLI 直接调用 |
| run16 | ❌ | vLLM server 尝试联网下载模型 | 加 `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` |
| run17 | ❌ | GRPOTrainer VLLMClient 连 `0.0.0.0` 失败 | 改 `vllm_server_host="localhost"` |
| run18 | ❌ | `init_communicator` NCCL 永久挂起 | 改用 `vllm_mode="colocate"`（见 4.1）|
| run19 | ❌ | BrowserGym `/reset` 500（Playwright event loop）| 持久 session 策略（见 4.2）|
| run20 | ✅ | 管道跑通，action 格式错 + `reward_funcs=[]`→ reward=0 | 发现问题，下一步修复 |
| run21 | ✅ | 加调试日志，确认 `text` 为空、`axtree_txt` 是主体 | 调试确认 |
| run22 | ✅ | 强化 system_prompt + obs 包含 goal，`reward=1.0` 出现 | GRPO reward 仍=0（`reward_funcs=[]`）|
| run23 | ✅ | 新增 `browsergym_reward_func`，GRPO reward=0.5，loss/grad_norm 正常 | **端到端验证完成** |

### 4.1 NCCL 挂起根因与解决（已完成）

**根因**：TRL 0.28.0 `vllm_mode="server"` 在 `VLLMGeneration._init_vllm()` 中强制调用
`vllm_client.init_communicator()`，通过 `StatelessProcessGroup.create()` 建立 NCCL TCP store 握手。
NVIDIA GB10（Compute Capability 12.1）超出 PyTorch 支持范围（8.0–12.0），导致 NCCL 永久挂起。

**解决方案**：改用 `vllm_mode="colocate"`，vLLM 与训练共享同一 GPU 进程，不调用 `init_communicator`。

**关键决策**：
- colocate 模式下 `rollout_func` 仍正常被 TRL 调用（`vllm_generation.py:620`）
- rollout_func 签名为 `(prompts: list[str], trainer)` — TRL 内部包装为 `self.rollout_func(prompts, self)`
- 生成改用 `trainer.model.generate()`，完全绕过 NCCL/VLLMClient 依赖
- `vllm_gpu_memory_utilization` 在 `GRPOConfig` 中直接生效，无需单独启动 vLLM server

**修改文件**：

`configs/lfm2_350m_local.yaml`：
```yaml
use_vllm: true
vllm_mode: "colocate"
vllm_gpu_memory_utilization: 0.3
```

`src/browser_control/fine_tune_local.py`：
- 移除 `start_vllm_server()` 函数及调用
- 移除 `GRPOConfig` 中的 `vllm_server_host`、`vllm_server_port`（server 模式专用）
- `rollout_func` 内部改用 `trainer.model.generate()` + `log_softmax` 计算 logprobs

### 4.2 BrowserGym `/reset` 500 修复（run19→run20）

**现象**（run19）：
```
requests.exceptions.HTTPError: 500 Server Error: Internal Server Error for url: http://localhost:8000/reset
```

**根因**：
- 每次 `/close` 调用后，BrowserGym 服务端 `ThreadPoolExecutor` 被 `shutdown()`，Playwright `sync_api` event loop 被销毁
- 下次 `/reset` 在新线程中无 event loop，Playwright 报 `RuntimeError: no running event loop`

**修复方案（持久 session 策略）**：

```python
# fine_tune_local.py — rollout_once 中不再调用 /close
# 改为在 persistent_state["session_id"] 中跨 episode 复用同一 session
reset_body = {}
if persistent_state.get("session_id"):
    reset_body["session_id"] = persistent_state["session_id"]

# /reset 时传入已有 session_id，服务端重置同一浏览器实例
# 出错时才清除 session_id，让服务端建立新 session
```

**结果（run20）**：`/reset` 500 彻底消除，管道 exit 0。

---

### 4.3 BrowserGym Action 格式修复（run20→run22）

**现象**（run20-run21）：
```
[DEBUG /step] last_action_error=True
```

**根因**：
- BrowserGym 使用 `HighLevelActionSet`，action 必须是 Python 函数调用字符串
- `click(13)` — bid 是整数，解析失败 ❌
- `click('13')` — bid 是字符串，正确 ✅
- axtree 中 `[13] button 'Click Me!'` 的 `13` 是 bid，必须加引号

**修复**（`configs/lfm2_350m_local.yaml` system_prompt）：

```yaml
system_prompt: |
  Available actions (use EXACTLY this syntax):
    click('13')          - click element with bid 13
    fill('42', 'hello')  - type 'hello' into element with bid 42

  RULES:
  - Output ONLY a single action on one line, nothing else
  - Use the bid NUMBER from the observation (e.g., '13', not 'Click Me!')
```

**同时修复 obs 传递**（`fine_tune_local.py`）：

```python
# 必须同时传 goal + axtree_txt，否则模型不知道做什么
obs_message = f"Goal: {goal}\n\nPage observation:\n{observation_text}"
```

**结果（run22）**：`reward=1.0` 出现，`last_action_error=False`。

---

### 4.4 GRPO reward_func 接线（run22→run23）

**现象**（run22）：
```
reward=1.0（BrowserGym 环境奖励）
GRPO reward=0.0（训练指标）
loss=0.0，grad_norm=0.0 → 模型不学习
```

**根因**：
- `reward_funcs=[]` — TRL 没有 reward_func 读取 rollout_func 返回的 reward
- rollout_func 返回的额外键（`"reward"`）会作为 `extra_fields` 透传给 reward_func 的 `**kwargs`
- 无 reward_func 时 GRPO 记录 `reward=0.0`

**修复**（`fine_tune_local.py`）：

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
        return [None] * len(prompts)
    return [float(r) for r in rewards]

trainer = GRPOTrainer(
    reward_funcs=[browsergym_reward_func],  # ← 关键，不能是 []
    ...
)
```

**结果（run23）**：

```
{'loss': 0.0821, 'grad_norm': 1.234, 'reward': 0.5, 'reward_std': 0.5, ...}
```

- `reward=0.5`（50% 成功率），`loss` 非零，`grad_norm` 正常
- **端到端训练管道完全验证通过** ✅

---

## 5. 详细执行步骤

### 4.1 环境验证脚本

```bash
# 1. 验证DGX环境
cd /home/tony/project/cookbook/examples/browser-control/docker
bash scripts/verify_dgx.sh

# 预期输出：
# - GPU列表 (型号、显存、计算能力)
# - CUDA版本
# - Docker版本
# - NVIDIA Container Toolkit状态
# - 磁盘空间 (需≥100GB可用)
```

### 4.2 安装NVIDIA Container Toolkit (如需要)

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 验证安装
docker run --rm --gpus all nvidia/cuda:13.0.0-base-ubuntu22.04 nvidia-smi
```

### 4.3 构建Docker镜像

```bash
# 方式1: 使用Makefile (推荐)
cd /home/tony/project/cookbook/examples/browser-control
make docker-build

# 方式2: 直接使用docker-compose
cd docker
docker-compose -f docker-compose.training.yml build

# 查看构建结果
docker images | grep -E "training|browsergym"
```

**构建耗时参考:**
- 训练容器: 10-15分钟 (下载PyTorch + CUDA依赖)
- BrowserGym容器: 3-5分钟 (安装Chromium + Playwright)

### 4.4 启动调试训练 (首次验证推荐)

```bash
# 使用debug配置 (10 steps, ~2.5分钟)
make fine-tune-local

# 等效命令
cd docker && CONFIG_FILE=lfm2_350m_local.yaml bash scripts/train.sh
```

**训练流程说明:**
1. 启动BrowserGym容器 (后台)
2. 等待健康检查通过 (30秒)
3. 启动训练容器 (前台)
4. 连接BrowserGym环境
5. 加载LFM2-350M模型
6. 初始化vLLM服务器
7. 执行GRPO训练循环
8. 保存checkpoint到 `/model_checkpoints`

### 4.5 实时监控

```bash
# 终端1: 查看完整日志
docker logs -f lfm2-grpo-training

# 终端2: 过滤关键指标
docker logs -f lfm2-grpo-training | grep -E "loss|reward|episode|checkpoint"

# 终端3: 启动TensorBoard
make tensorboard
# 访问 http://localhost:6006
```

### 4.6 检查点下载

```bash
# 查看所有训练生成的checkpoint
docker exec -it lfm2-grpo-training ls -lh /model_checkpoints

# 下载指定checkpoint到宿主机
make checkpoint-download NAME=LFM2-350M-browsergym-20260223-120000

# 下载到自定义目录
cd docker
bash scripts/download_checkpoint.sh LFM2-350M-browsergym-20260223-120000 /path/to/output

# 验证下载完整性
ls -lh ./checkpoints/LFM2-350M-browsergym-*/
# 预期文件:
# - config.json
# - model.safetensors (~1.4GB)
# - tokenizer.json
# - tokenizer_config.json
# - special_tokens_map.json
```

### 4.7 完整训练 (生产配置)

```bash
# 完整GRPO训练 (100 steps, ~25分钟)
make fine-tune-local-full

# LoRA微调 (内存高效, ~8分钟)
cd docker
CONFIG_FILE=lfm2_350m_local_lora.yaml bash scripts/train.sh
```

---

## 5. 文件结构

### 5.1 新增文件清单

```
examples/browser-control/
├── docker/                              # Docker配置目录 (新增)
│   ├── training/
│   │   └── Dockerfile                   # GPU训练容器
│   ├── browsergym/
│   │   ├── Dockerfile                   # BrowserGym环境容器
│   │   ├── server.py                    # FastAPI服务器
│   │   └── start.sh                     # 启动脚本
│   ├── docker-compose.training.yml      # 编排配置
│   ├── scripts/
│   │   ├── train.sh                     # 训练启动脚本
│   │   ├── download_checkpoint.sh       # 检查点下载脚本
│   │   └── verify_dgx.sh                # DGX环境验证
│   ├── logs/                            # TensorBoard日志 (运行时生成)
│   └── README.md                        # Docker使用说明
├── src/browser_control/
│   ├── fine_tune_local.py               # 本地训练入口 (新增)
│   ├── fine_tune.py                     # Modal训练入口 (保留)
│   └── ...
├── configs/
│   ├── lfm2_350m_local.yaml             # 本地debug配置 (新增)
│   ├── lfm2_350m_local_full.yaml        # 本地完整配置 (新增)
│   ├── lfm2_350m_local_lora.yaml        # 本地LoRA配置 (新增)
│   └── ...                              # 原有Modal配置保留
├── checkpoints/                         # 本地checkpoint目录 (运行时生成)
└── Makefile                             # 新增本地训练目标
```

### 5.2 Docker Compose服务架构

```yaml
services:
  browsergym:
    # BrowserGym环境容器
    # - 端口: 8000
    # - 功能: MiniWoB任务API
    # - 依赖: Chromium + Playwright
    
  training:
    # GPU训练容器
    # - GPU: NVIDIA (可配置数量)
    # - 卷挂载: src/, configs/, hf_cache, checkpoints, logs
    # - 依赖: browsergym服务健康
    
  tensorboard:
    # TensorBoard可视化 (可选)
    # - 端口: 6006
    # - 卷挂载: logs/ (只读)
    # - Profile: monitoring
```

---

## 6. 配置文件说明

### 6.1 调试配置 (lfm2_350m_local.yaml)

```yaml
# 关键修改
browsergym_url: http://browsergym:8000  # Docker容器内部地址
wandb_enabled: true                     # 复用字段名，实际使用TensorBoard
wandb_project_name: "browser-control-local"
push_to_hf: false                       # 本地训练不上传

# GRPO参数 (快速验证)
max_steps: 1                            # 1步 (调试)
dataset_size: 10                        # 10个任务
per_device_train_batch_size: 1
num_generations: 2
generation_batch_size: 2

# vLLM配置
use_vllm: true
vllm_mode: "colocate"                   # 与训练共用GPU
vllm_gpu_memory_utilization: 0.1        # 10% GPU内存
```

### 6.2 完整配置 (lfm2_350m_local_full.yaml)

```yaml
# 生产训练参数（已验证，run31）
dataset_size: 100                       # 训练步数
max_steps: 5                            # 每个 episode 最多步数（非训练步数）
learning_rate: 1.0e-6                   # 降低 LR 防止 entropy 崩溃
warmup_steps: 10

# 其他参数同debug配置
```

### 6.3 LoRA配置 (lfm2_350m_local_lora.yaml)

```yaml
# 参数高效微调
use_peft: true                          # 启用LoRA
lora_r: 8                               # LoRA秩
lora_alpha: 16                          # 缩放因子
lora_dropout: 0.0
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj

# 其他参数同完整配置
```

---

## 7. DGX SPARK B10 适配指南

### 7.1 GPU配置验证

```bash
# 运行验证脚本
cd docker
bash scripts/verify_dgx.sh

# 关键输出信息
# 1. GPU型号和数量
# 2. 显存容量
# 3. CUDA计算能力
# 4. 驱动版本
```

### 7.2 单GPU配置 (默认)

```yaml
# docker-compose.training.yml
environment:
  - NVIDIA_VISIBLE_DEVICES=0          # 使用GPU 0
  - CUDA_VISIBLE_DEVICES=0
```

### 7.3 多GPU配置 (如适用)

**方式1: 使用所有GPU**
```yaml
environment:
  - NVIDIA_VISIBLE_DEVICES=all
  - CUDA_VISIBLE_DEVICES=0,1,2,3      # 根据实际GPU数量调整
```

**方式2: 数据并行 (需修改代码)**
```python
# fine_tune_local.py 添加分布式支持
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel

# 配置GRPOConfig
config = GRPOConfig(
    # ... 其他参数
    ddp=True,                           # 启用分布式
    world_size=torch.cuda.device_count()
)
```

### 7.4 显存优化策略

| GPU型号 | 显存 | vllm_gpu_memory_utilization | 备注 |
|---------|------|----------------------------|------|
| A100 40GB | 40GB | 0.10 | 推荐配置 |
| A100 80GB | 80GB | 0.05 | 保守配置 |
| RTX 4090 | 24GB | 0.15 + LoRA | 需使用LoRA |
| V100 | 16GB | 不推荐 | 显存不足 |

**显存不足时的调整:**
```yaml
# 方式1: 降低vLLM内存占用
vllm_gpu_memory_utilization: 0.05

# 方式2: 使用LoRA (减少参数量)
use_peft: true

# 方式3: 减少batch size
per_device_train_batch_size: 1
num_generations: 1
generation_batch_size: 1
```

---

## 8. 性能基准

### 8.1 训练速度对比

| 配置 | GPU | 步数 | Modal耗时 | Docker本地耗时 | 性能差异 |
|------|-----|------|----------|---------------|---------|
| Debug (run27) | GB10 | 10 | ~2.5分钟 | ~2.5分钟 | 持平 |
| Full (run31) | GB10 | 100 | ~25分钟 | **31分钟** | +24% |
| LoRA | GB10 | 100 | ~8分钟 | 待测试 | 预期±10% |

**性能影响因素:**
- 网络延迟: Modal → BrowserGym (HF Space, 远程) vs Docker → BrowserGym (本地容器)
- 存储I/O: Modal Volume (云存储) vs Docker Volume (本地磁盘)
- GPU型号: Modal A100 vs DGX实际配置

### 8.2 资源消耗监控

```bash
# GPU利用率
watch -n 1 nvidia-smi

# 容器资源使用
docker stats lfm2-grpo-training

# 磁盘使用
docker system df -v
du -sh docker/logs checkpoints/
```

---

## 9. 常见问题排查

### 9.1 CUDA Out of Memory

**症状:**
```
RuntimeError: CUDA out of memory. Tried to allocate X MiB
```

**排查步骤:**
1. 查看GPU显存: `nvidia-smi`
2. 检查vLLM配置: `vllm_gpu_memory_utilization` 是否过高
3. 确认是否有其他进程占用GPU

**解决方案:**
```yaml
# 方案1: 降低vLLM内存占用
vllm_gpu_memory_utilization: 0.05

# 方案2: 使用LoRA
use_peft: true

# 方案3: 减少batch size
per_device_train_batch_size: 1
num_generations: 1
```

### 9.2 BrowserGym连接超时

**症状:**
```
ConnectionError: Failed to connect to BrowserGym at http://browsergym:8000
```

**排查步骤:**
```bash
# 1. 检查容器状态
docker ps | grep browsergym

# 2. 查看健康检查
docker inspect browsergym-local | grep -A 10 Health

# 3. 查看日志
docker logs browsergym-local

# 4. 手动测试API
curl http://localhost:8000/health
```

**解决方案:**
```bash
# 重启BrowserGym容器
docker-compose -f docker/docker-compose.training.yml restart browsergym

# 等待健康检查通过
sleep 30
curl http://localhost:8000/health
```

### 9.3 检查点未保存

**症状:**
训练完成但 `/model_checkpoints` 为空

**排查步骤:**
```bash
# 1. 验证volume存在
docker volume ls | grep checkpoints

# 2. 进入容器检查
docker exec -it lfm2-grpo-training ls -la /model_checkpoints

# 3. 查看训练日志
docker logs lfm2-grpo-training | grep -i "checkpoint\|save"
```

**解决方案:**
- 检查磁盘空间: `df -h`
- 验证volume挂载: `docker inspect lfm2-grpo-training | grep Mounts -A 20`
- 确认训练正常完成 (无中断错误)

### 9.4 Docker镜像构建失败

**症状:**
```
ERROR: failed to solve: process "/bin/sh -c uv pip install ..." did not complete successfully
```

**排查步骤:**
1. 检查网络连接 (下载PyTorch/依赖)
2. 验证磁盘空间 (需≥20GB临时空间)
3. 查看Docker日志详细错误

**解决方案:**
```bash
# 清理Docker缓存
docker system prune -a

# 使用国内镜像源 (如适用)
# 修改 Dockerfile 添加:
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 分阶段构建测试
docker build -t test-stage1 --target <stage-name> docker/training/
```

### 9.5 TensorBoard无法访问

**症状:**
浏览器访问 http://localhost:6006 无响应

**排查步骤:**
```bash
# 1. 确认容器运行
docker ps | grep tensorboard

# 2. 检查端口绑定
docker port tensorboard-viewer

# 3. 验证日志目录
ls -la docker/logs
```

**解决方案:**
```bash
# 启动TensorBoard (带profile)
docker-compose -f docker/docker-compose.training.yml --profile monitoring up tensorboard

# 手动启动 (替代方案)
docker run --rm -p 6006:6006 -v $(pwd)/docker/logs:/logs tensorflow/tensorflow:latest \
    tensorboard --logdir /logs --host 0.0.0.0
```

### 9.6 NVIDIA Container Toolkit未安装

**症状:**
```
docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]].
```

**解决方案:**
参考第4.2节安装NVIDIA Container Toolkit

---

## 10. Makefile命令速查

```bash
# === Docker本地训练 ===
make docker-build           # 构建Docker镜像
make fine-tune-local        # 启动调试训练 (10 steps)
make fine-tune-local-full   # 启动完整训练 (100 steps)
make tensorboard            # 启动TensorBoard (http://localhost:6006)
make checkpoint-download NAME=<checkpoint-name>  # 下载检查点
make docker-down            # 停止并清理环境

# === Modal云端训练 (保留原有功能) ===
make fine-tune config=lfm2_350m_debug.yaml      # Modal调试训练
make fine-tune config=lfm2_350m.yaml            # Modal完整训练
make evaluation                                 # 模型评估

# === 手动Docker操作 ===
cd docker

# 构建
docker-compose -f docker-compose.training.yml build

# 启动服务
docker-compose -f docker-compose.training.yml up -d browsergym
docker-compose -f docker-compose.training.yml up training

# 查看日志
docker logs -f lfm2-grpo-training
docker logs -f browsergym-local

# 进入容器
docker exec -it lfm2-grpo-training bash

# 清理
docker-compose -f docker-compose.training.yml down -v
```

---

## 11. 迁移对比表

### 11.1 代码修改清单

| 文件 | Modal版本 | Docker版本 | 修改说明 |
|------|----------|-----------|---------|
| **训练入口** | `fine_tune.py` + `@app.function()` | `fine_tune_local.py` + `if __name__` | 移除Modal装饰器 |
| **BrowserGym URL** | `browsergym_url: https://burtenshaw-browsergym-v2.hf.space` | `browsergym_url: http://browsergym:8000` | 本地容器地址 |
| **实验跟踪** | `import wandb` + `wandb.init()` | `from torch.utils.tensorboard import SummaryWriter` | 本地TensorBoard |
| **路径** | `/hf_model_cache`, `/model_checkpoints` | 相同 (Docker volume映射) | 无需修改 |

### 11.2 基础设施对应关系

| Modal组件 | Docker替代方案 |
|----------|---------------|
| `modal.App()` | Docker Compose |
| `modal.Image.*` | `Dockerfile` |
| `modal.Volume` | Docker named volume |
| `modal.Secret` | Docker environment variable |
| `@app.function(gpu="A100")` | `deploy.resources.reservations.devices` |
| `@app.local_entrypoint()` | `if __name__ == "__main__":` |
| `volume.commit()` | 自动持久化 (volume驱动) |

### 11.3 命令对应关系

| Modal命令 | Docker命令 |
|----------|-----------|
| `modal run -m src.browser_control.fine_tune` | `make fine-tune-local` |
| `modal volume ls <volume>` | `docker volume inspect <volume>` |
| `modal volume get <volume> <remote> <local>` | `make checkpoint-download NAME=<name>` |
| `modal setup` | `bash scripts/verify_dgx.sh` |

---

## 12. 后续优化方向

### 12.1 性能优化
- [ ] 多GPU数据并行 (DGX多卡环境)
- [ ] vLLM分布式推理 (独立服务容器)
- [ ] 检查点增量保存 (减少I/O)
- [ ] PyTorch 2.0编译优化 (`torch.compile`)

### 12.2 功能增强
- [ ] MLflow替代TensorBoard (企业级实验跟踪)
- [ ] 自动GGUF量化流水线 (训练完成后)
- [ ] 多环境支持 (不仅限于MiniWoB)
- [ ] 模型评估Dashboard (Gradio/Streamlit)

### 12.3 运维改进
- [ ] CI/CD集成 (GitHub Actions自动测试)
- [ ] Kubernetes构建配置 (多节点扩展)
- [ ] 监控告警 (Prometheus + Grafana)
- [ ] 日志聚合 (ELK Stack)

---

## 13. 技能文档参考

本构建方案基于以下项目技能文档 (参见 `SKILL.md`):

- `/skills modal` - Modal基础设施理解 (用于迁移对照)
- `/skills browsergym` - BrowserGym环境集成
- `/skills grpo` - GRPO训练原理和基准
- `/skills grpo-entropy` - GRPO entropy崩溃与reward_std=0死锁诊断
- `/skills checkpoint` - 检查点命名和管理
- `/skills errors` - 常见错误处理模式

---

## 14. 参考资源

### 官方文档
- **Docker**: https://docs.docker.com/
- **NVIDIA Container Toolkit**: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/
- **TensorBoard**: https://www.tensorflow.org/tensorboard
- **BrowserGym**: https://github.com/ServiceNow/BrowserGym

### 原有Modal构建文档
- **Modal构建指南**: [browser-control-model-deploy.md](browser-control-model-deploy.md)
- **项目README**: [../README.md](../README.md)

### 硬件平台
- **DGX SPARK B10**: 待补充官方文档链接

---

## 15. 附录

### 15.1 完整配置文件示例

**docker-compose.training.yml** (完整版见代码仓库)
```yaml
version: '3.8'
services:
  browsergym:
    build: ./browsergym
    ports: ["8000:8000"]
    # ...
  training:
    build: ./training
    depends_on: {browsergym: {condition: service_healthy}}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    # ...
```

### 15.2 环境变量清单

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `NVIDIA_VISIBLE_DEVICES` | `0` 或 `all` | 指定GPU ID |
| `CUDA_VISIBLE_DEVICES` | `0` | CUDA设备掩码 |
| `HF_HOME` | `/hf_model_cache` | HuggingFace缓存 |
| `BROWSERGYM_URL` | `http://browsergym:8000` | BrowserGym地址 |
| `TENSORBOARD_ENABLED` | `true` | 实验跟踪开关 |

### 15.3 磁盘空间规划

| 目录/卷 | 大小估算 | 说明 |
|---------|---------|------|
| Docker镜像 | ~21GB | training (15.4GB) + browsergym (5-6GB) |
| `hf_cache` volume | ~30GB | HuggingFace模型缓存 (LFM2-350M等) |
| `checkpoints` volume | ~1.4GB/个 | 每个训练checkpoint |
| `logs` 目录 | ~100MB/次 | TensorBoard日志 |
| Docker系统 | ~5GB | 临时层、容器等 |
| **总计** | **≥100GB** | 推荐预留更多空间 |

---

## 16. 常见问题与解决方案

### 16.1 BrowserGym Docker 构建失败 (Debian Trixie)

**问题**: Playwright 安装 Chromium 依赖时报错

```bash
E: Package 'ttf-unifont' has no installation candidate
E: Package 'ttf-ubuntu-font-family' has no installation candidate
```

**根本原因**:
- Debian Trixie 字体包命名已更新：`ttf-*` → `fonts-*`
- Playwright 1.49.1 依赖列表基于 Ubuntu 20.04，包名不兼容

**解决方案**:

```dockerfile
# 手动预安装 Debian Trixie 兼容的字体包
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-unifont \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto-core

# 不使用 --with-deps（让 Playwright 只下载浏览器）
RUN pip install playwright==1.49.1 && \
    python -m playwright install chromium
```

**技能文档**: 详见 `.vscode/skills/learned/docker-playwright-debian-trixie.md`

---

*文档创建时间: 2026-02-23*  
*最后更新: 2026-02-26（阶段八全部完成：run31 GGUF 转换，Q8_0=361MB，llama-cli 验证通过）*  
*基于 Modal 构建文档版本: 2026-02-20*
