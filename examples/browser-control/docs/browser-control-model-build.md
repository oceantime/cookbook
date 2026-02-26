# browser-control 构建指南

> **最后更新**: 2026-02-20 (Stage 5 完成)
> **环境管理**: 仅使用 `uv`（不使用 conda）

## 1. 项目概述

基于 Liquid AI 的 cookbook 示例，使用 **GRPO 强化学习算法** 训练 **LFM2-350M** 模型进行浏览器自动化控制。

### 核心技术栈
- **模型**: LFM2-350M (Liquid AI)
- **RL 算法**: GRPO (Group Relative Policy Optimization)
- **环境**: BrowserGym (MiniWoB 基准测试) via OpenEnv (`envs` 模块)
- **推理**: vLLM
- **基础设施**: Modal (serverless GPU, workspace: `oceantime`)
- **微调**: 支持 Full Fine-tune 和 LoRA
- **实验跟踪**: Weights & Biases

---

## 2. 环境要求

| 组件 | 版本/要求 | 备注 |
|------|----------|------|
| Python | 3.12 (.python-version) | uv 自动管理 |
| GPU | A100 (已验证) | Modal 远程执行 |
| 包管理器 | uv >= 0.10.3 | **不使用 conda** |
| Modal CLI | >= 1.2.5 | 作为项目依赖安装 |

### 核心依赖 (pyproject.toml 实际版本)
```
trl >= 0.25.1            # GRPO 训练器（实际 0.25.1）
transformers >= 4.57.3    # HuggingFace 模型（实际 4.57.3）
openenv (git source)     # RL 环境，import 名为 envs（非 openenv）
modal >= 1.2.5           # 云端 GPU 基础设施（实际 1.2.5）
peft >= 0.13.0           # LoRA 微调（实际 0.18.0）
wandb >= 0.23.1          # 实验跟踪
torch                    # PyTorch（实际 2.9.1）
```

---

## 3. 构建任务清单（已验证状态）

### 阶段一：环境准备 ✅ 完成
- [x] 安装 uv 包管理器 (v0.10.3)
- [x] 进入项目目录 `cd examples/browser-control`
- [x] 运行 `uv sync` 安装依赖 (121 packages)
- [x] 验证 Python 3.12.3
- [x] 验证核心 import: trl, transformers, peft, modal, torch, BrowserGymEnv
- [x] 安装 `socksio` 修复 SOCKS 代理 + httpx 问题: `uv pip install httpx[socks]`

### 阶段二：配置设置 ✅ 完成
- [x] Modal CLI 认证成功 (workspace: `oceantime`)
- [x] 创建 Modal Secret `wandb-secret`（需 40+ 字符有效 API key）
- [x] 所有 5 个 YAML 配置文件解析成功验证
- [x] 可选配置：
  - `lfm2_350m.yaml` - 完整微调
  - `lfm2_350m_lora.yaml` - LoRA 微调
  - `lfm2_350m_debug.yaml` - 调试配置 ← **已用于首次训练**
  - `lfm2_350m_book_flight.yaml` - 复杂任务
  - `functiongemma_270m.yaml` - Google FunctionGemma 模型

### 阶段三：基础设施验证 ✅ 完成
- [x] BrowserGym HF Spaces 确认 RUNNING（注意：根路径 `/` 返回 404 是正常的，服务在 `/web` 和 `/docs` 子路径）
- [x] Modal API 连接已验证
- [x] Modal GPU (A100) 访问已验证（通过实际训练）

### 阶段四：训练执行 ✅ 完成
- [x] 使用 debug 配置运行训练: `make fine-tune config=lfm2_350m_debug.yaml`
- [x] 训练成功完成: 10 步, ~2.5 分钟 (A100)
- [x] 模型检查点已保存（见下方「模型保存路径」）
- [x] WandB 实验跟踪: https://wandb.ai/27575910-/browser-control-fine-tune-with-grpo/runs/fiakggw3
- [ ] （可选）运行完整微调 `lfm2_350m.yaml`
- [ ] （可选）运行 LoRA 微调 `lfm2_350m_lora.yaml`

#### 模型保存路径
**Modal Volume (云端)**
- Volume 名称: `browser-control-fine-tune-with-grpo`
- 完整路径: `/model_checkpoints/LFM2-350M-browsergym-20260220-182152`
- 访问方式: `uv run modal volume ls browser-control-fine-tune-with-grpo`

**本地路径（下载后）**
- 本地目录: `checkpoints/LFM2-350M-browsergym-20260220-182152`
- 模型大小: ~1.4GB
- 下载命令: 见下方第10节

**WandB Artifacts（可选）**
- 项目: `browser-control-fine-tune-with-grpo`
- Run ID: `fiakggw3`
- 如启用 artifact 上传，可在 WandB 项目页面下载

### 阶段五：评估测试 ✅ 完成
- [x] 评估脚本验证: `make evaluation` 或手动运行 Python 模块
- [x] BrowserGym 环境连接正常 (HF Space: burtenshaw-browsergym-v2)
- [x] 作者模型 (Paulescu/LFM2-350M-browsergym-20251224-013119) 评估通过
- [x] 本地 checkpoint 下载成功 (1.4GB): `checkpoints/LFM2-350M-browsergym-20260220-182152`
- [x] 本地 checkpoint 加载验证通过 (354.5M params)
- [ ] （可选）尝试 `book-flight` 等更复杂任务

### 评估结果记录
| 模型 | 状态 | 说明 |
|------|------|------|
| Paulescu/LFM2-350M-browsergym-20251224-013119 | ✅ 通过 | 生成 click('13') 动作 |
| LFM2-350M-browsergym-20260220-182152 (本地) | ✅ 通过 | 加载验证 354.5M params |

> 注意: 评估脚本 `evaluate.py` 需要较长时间运行（需要下载模型、连接 BrowserGym 环境）。

---

## 4. 执行命令

```bash
# 1. 进入项目目录
cd /home/tony/project/cookbook/examples/browser-control

# 2. 安装依赖（创建 .venv 并安装所有包）
uv sync

# 3. 修复 SOCKS 代理问题（如果环境使用 SOCKS 代理）
uv pip install httpx[socks]

# 4. 验证 Modal 认证
uv run modal profile current

# 5. 运行 debug 训练（首次验证推荐）
make fine-tune config=lfm2_350m_debug.yaml

# 6. 运行完整微调
make fine-tune config=lfm2_350m.yaml

# 7. 运行 LoRA 微调（资源节省推荐）
make fine-tune config=lfm2_350m_lora.yaml

# 8. 运行评估
make evaluation
```

> **注意**: `modal` CLI 是项目依赖，通过 `uv run modal` 或激活 `.venv` 后调用。不需要全局安装。

---

## 5. 已发现问题与修复

### 5.1 SOCKS 代理 + httpx
**问题**: 环境配置了 SOCKS 代理，导致 httpx 初始化失败。
**修复**: `uv pip install httpx[socks]`（安装 `socksio`）

### 5.2 evaluate.py 配置文件名错误
**问题**: `evaluate.py:10` 引用了不存在的 `lfm2_350m_debugging.yaml`
**修复**: 改为 `lfm2_350m_debug.yaml`

### 5.3 openenv 包名 vs 模块名
**问题**: pip 包名为 `openenv`，但 import 模块名为 `envs`（不是 `openenv`）
**代码**: `from envs.browsergym_env import BrowserGymEnv` ← 正确用法

### 5.4 BrowserGym HF Space 根路径 404
**问题**: 访问 HF Space 根 URL 返回 404，容易误认为服务宕机
**说明**: API 服务运行在 `/web` 和 `/docs` 子路径，根路径 404 是正常行为。使用 HF API 检查实际运行状态。

### 5.5 WandB Secret 格式
**问题**: Modal Secret `wandb-secret` 中的 API key 必须是有效的 40+ 字符 key
**修复**: 在 Modal Dashboard 更新 secret 值

---

## 6. Modal 资源

### Volumes
| 名称 | 用途 |
|------|------|
| `browser-control-fine-tune-with-grpo` | 模型检查点存储 |
| `hf-model-cache` | HuggingFace 模型缓存 |

### Secrets
| 名称 | 用途 |
|------|------|
| `wandb-secret` | WandB API Key (WANDB_API_KEY) |

---

## 7. 预期资源消耗

| 任务类型 | GPU | 时间 | 备注 |
|---------|-----|------|------|
| click-test (debug, 10步) | A100 | ~2.5 分钟 | **已验证** |
| click-test (完整微调) | A100 | 10-30 分钟 | 待测试 |
| click-test (LoRA) | A100 | 5-15 分钟 | 待测试 |
| book-flight (复杂任务) | A100 | 1-3 小时 | 待测试 |

---

## 8. 项目架构

```
browser-control/
├── configs/                    # YAML 配置文件
│   ├── lfm2_350m.yaml         # 完整微调配置
│   ├── lfm2_350m_lora.yaml    # LoRA 配置
│   ├── lfm2_350m_debug.yaml   # 调试配置（已验证）
│   ├── lfm2_350m_book_flight.yaml  # 复杂任务配置
│   └── functiongemma_270m.yaml     # Google FunctionGemma 配置
├── src/browser_control/       # 主要代码
│   ├── fine_tune.py          # 训练脚本 (Modal remote)
│   ├── evaluate.py           # 评估脚本 (本地运行)
│   ├── config.py             # 配置管理 (Pydantic)
│   ├── modal_infra.py        # Modal 基础设施定义
│   └── paths.py              # 路径工具
├── docs/                      # 文档
├── media/                     # 截图和可视化资源
├── Makefile                   # 构建命令
├── pyproject.toml            # 项目依赖
├── .python-version           # Python 版本 (3.12)
├── .envrc                    # direnv 配置
└── README.md                 # 项目文档
```

---

## 9. 核心组件说明

### 9.1 GRPO 算法
GRPO (Group Relative Policy Optimization) 使用组内相对性能来确定强化方向：
- 比组内其他表现好的响应获得正优势
- 表现差的获得负优势
- 比 PPO 更内存高效（无需训练价值模型）

### 9.2 训练流程
1. 模型观察环境状态（网页 DOM / AXTree）
2. 生成动作（点击、输入、滚动等）
3. 执行动作并获得奖励
4. GRPO 根据奖励调整模型参数

### 9.3 三大组件
1. **GRPOTrainer** (trl): 实现 GRPO 算法，运行在 Modal A100 GPU 上
2. **vLLM Server**: 生成模型 rollout，与 trainer 共用 GPU
3. **BrowserGym** (HF Space): RL 环境，远程运行在 HuggingFace Spaces

---

## 10. 模型检查点管理

### 10.1 Modal Volume 存储结构
训练过程中，模型自动保存到 Modal volume:
```
Modal Volume: browser-control-fine-tune-with-grpo
└── /model_checkpoints/
    └── LFM2-350M-browsergym-20260220-182152/  # 格式: {model_name}-{task}-{timestamp}
        ├── config.json
        ├── model.safetensors
        ├── tokenizer.json
        ├── tokenizer_config.json
        └── special_tokens_map.json
```

### 10.2 查看 Modal Volume 内容
```bash
# 列出所有训练的 checkpoint
uv run modal volume ls browser-control-fine-tune-with-grpo model_checkpoints

# 查看特定 checkpoint 详情
uv run modal volume ls browser-control-fine-tune-with-grpo model_checkpoints/LFM2-350M-browsergym-20260220-182152
```

### 10.3 下载到本地
```bash
# 创建本地目录
mkdir -p checkpoints

# 下载完整 checkpoint (约 1.4GB)
uv run modal volume get browser-control-fine-tune-with-grpo \
  model_checkpoints/LFM2-350M-browsergym-20260220-182152 \
  ./checkpoints/

# 下载后本地路径
# ./checkpoints/LFM2-350M-browsergym-20260220-182152/
```

### 10.4 上传现有模型到 Modal Volume
```bash
# 如需上传本地模型到 Modal volume
uv run modal volume put browser-control-fine-tune-with-grpo \
  ./local_model_path \
  model_checkpoints/my-custom-model
```

### 10.5 在评估中使用模型
```python
# 评估时可以使用：
# 1. Modal volume 路径（云端）
checkpoint_path = "modal://browser-control-fine-tune-with-grpo/model_checkpoints/LFM2-350M-browsergym-20260220-182152"

# 2. 本地路径（已下载）
checkpoint_path = "./checkpoints/LFM2-350M-browsergym-20260220-182152"

# 3. HuggingFace Hub（已上传）
checkpoint_path = "Paulescu/LFM2-350M-browsergym-20251224-013119"
```

## 11. 参考资源

- **官方文档**: https://docs.liquid.ai/examples/laptop-examples/browser-control
- **项目源码**: https://github.com/Liquid4All/cookbook/tree/main/examples/browser-control
- **MiniWoB 任务列表**: https://miniwob.farama.org/environments/list/
- **Modal 文档**: https://modal.com/docs
- **WandB 训练记录**: https://wandb.ai/27575910-/browser-control-fine-tune-with-grpo/runs/fiakggw3

---

*文档更新时间: 2026-02-20*
