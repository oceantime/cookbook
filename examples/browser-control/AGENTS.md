# browser-control 开发指南

> **最后更新**: 2026-02-22  
> **目的**: AI 代理执行 browser-control 项目任务前的预读文档  
> **项目**: 使用 LFM2-350M + GRPO 强化学习的浏览器自动化

---

## 📋 快速参考

### 项目状态
- ✅ **训练管道**: 运行正常（Modal + GRPO）
- ✅ **模型转换**: 两种方法（本地 ARM64 + Modal 云端）
- ⏳ **Android 构建**: 阶段一完成，阶段二及以后待进行

### 关键命令
```bash
# 训练
make fine-tune config=lfm2_350m_debug.yaml    # 调试模式
make fine-tune config=lfm2_350m.yaml          # 完整微调
make fine-tune config=lfm2_350m_lora.yaml     # LoRA 微调

# 评估
make evaluation                                # 运行浏览器任务评估

# 模型转换（选择其一）
uv run python scripts/convert_to_gguf_local.py    # 本地 ARM64+CUDA13（2-3秒）
uv run modal run scripts/convert_to_gguf_simple.py # Modal 云端（5-8分钟）
```
---

## 🗂️ 项目架构

```
browser-control/
├── configs/                              # 训练配置文件
│   ├── lfm2_350m.yaml                   # 完整微调（生产环境）
│   ├── lfm2_350m_lora.yaml              # LoRA 微调（高效）
│   ├── lfm2_350m_debug.yaml             # 调试配置（10步，已验证）
│   ├── lfm2_350m_book_flight.yaml       # 复杂任务基准
│   └── functiongemma_270m.yaml          # Google FunctionGemma 模型
│
├── src/browser_control/                 # 主要代码库
│   ├── fine_tune.py                     # GRPO 训练（Modal 远程）
│   ├── evaluate.py                      # 任务评估（本地）
│   ├── config.py                        # 配置管理（Pydantic）
│   ├── modal_infra.py                   # Modal 基础设施
│   └── paths.py                         # 路径工具
│
├── scripts/                             # 实用脚本
│   ├── convert_to_gguf_local.py        # 本地 GGUF 转换（ARM64+CUDA13）
│   └── convert_to_gguf_simple.py       # Modal GGUF 转换（x86_64+A10G）
│
├── docs/                                # 文档
│   ├── browser-control-model-deploy.md     # 训练构建指南
│   └── browser-control-android-deploy.md   # Android 构建计划
│
├── checkpoints/                         # 下载的模型检查点
├── gguf_models/                         # GGUF 模型（Modal 转换）
├── gguf_models_local/                   # GGUF 模型（本地转换）
├── media/                               # 截图和可视化资源
│
├── Makefile                             # 构建自动化
├── pyproject.toml                       # 依赖项（uv 管理）
├── .python-version                      # Python 3.12
├── .envrc                               # direnv 配置
│
├── AGENTS.md                            # ← 本文件（AI 代理指南）
├── SKILL.md                             # 项目技能文档
└── README.md                            # 面向用户的文档
```

---

## 🎯 核心组件

### 1. 训练管道（Modal + GRPO）

**技术栈**:
- **模型**: LFM2-350M（Liquid AI，354.5M 参数）
- **算法**: GRPO（组相对策略优化）
- **环境**: BrowserGym（MiniWoB 基准测试）
- **推理**: vLLM 服务器
- **基础设施**: Modal（无服务器 A100 GPU）
- **跟踪**: Weights & Biases

**工作流程**:
1. 模型观察浏览器状态（DOM/AXTree）
2. 生成动作（点击、输入、滚动）
3. 在 BrowserGym 环境中执行
4. 接收奖励（任务完成情况）
5. GRPO 更新策略参数

**关键文件**:
- `src/browser_control/fine_tune.py`: 主训练循环
- `src/browser_control/modal_infra.py`: GPU 基础设施设置
- `configs/*.yaml`: 训练超参数

### 2. 模型转换管道（GGUF）

**目的**: 将 HuggingFace 检查点转换为 GGUF 格式用于移动构建（Android LeapSDK）

**两种方法**:

| 方法 | 环境 | 速度 | 使用场景 |
|------|------|------|----------|
| **本地** | ARM64 + CUDA 13.0 | ⚡ 2-3秒 | 开发迭代 |
| **Modal** | x86_64 + A10G | 🐢 5-8分钟 | 跨平台兼容性 |

**工具**: llama.cpp（`convert_hf_to_gguf.py` + `llama-quantize`）

**输出**:
- FP16: 678MB（基础）
- Q8_0: 362MB（生产环境推荐）
- Q5_K_M: 249MB（平衡）
- Q4_K_M: 219MB（低端设备）

**关键文件**:
- `scripts/convert_to_gguf_local.py`: 本地转换（CUDA 13.0）
- `scripts/convert_to_gguf_simple.py`: Modal 云端转换

### 3. 评估系统

**目的**: 在 MiniWoB 任务上验证训练的模型

**环境**: BrowserGym HF Space（burtenshaw-browsergym-v2）

**任务**:
- `click-test`: 点击特定按钮
- `book-flight`: 复杂的多步骤工作流

**关键文件**:
- `src/browser_control/evaluate.py`: 评估运行器

---

## 🚀 开发工作流

### 阶段一：环境设置

```bash
cd /home/tony/project/cookbook/examples/browser-control

# 安装依赖（使用 uv，不使用 conda）
uv sync

# 修复 SOCKS 代理问题（如需要）
uv pip install httpx[socks]

# 验证 Modal 认证
uv run modal profile current  # 应显示：oceantime
```

### 阶段二：训练

```bash
# 快速验证（10步，约2.5分钟）
make fine-tune config=lfm2_350m_debug.yaml

# 完整训练（约10-30分钟）
make fine-tune config=lfm2_350m.yaml

# LoRA 训练（高效，约5-15分钟）
make fine-tune config=lfm2_350m_lora.yaml
```

**输出**:
- Modal Volume: `browser-control-fine-tune-with-grpo/model_checkpoints/`
- WandB: https://wandb.ai/27575910-/browser-control-fine-tune-with-grpo

### 阶段三：模型下载

```bash
# 列出可用检查点
uv run modal volume ls browser-control-fine-tune-with-grpo model_checkpoints

# 下载到本地（示例：LFM2-350M-browsergym-20260220-182152）
mkdir -p checkpoints
uv run modal volume get browser-control-fine-tune-with-grpo \
  model_checkpoints/LFM2-350M-browsergym-20260220-182152 \
  ./checkpoints/
```

### 阶段四：模型转换（用于 Android）

**⚠️ 前置条件**:
- **本地方法**: ARM64 系统 + CUDA 13.0 驱动 + llama.cpp 已编译
- **Modal 方法**: 有余额的 Modal 账户

**选择方法**:

<details>
<summary><b>方法一：本地（ARM64 + CUDA 13.0）</b></summary>

```bash
# 1. 配置 pyproject.toml（如果尚未完成）
# 添加 pytorch-cu130 索引配置

# 2. 安装依赖
uv sync

# 3. 验证 CUDA
uv run python -c "import torch; print(torch.cuda.is_available())"
# 应输出：True

# 4. 编译 llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build && cmake --build build --config Release -j$(nproc)
cd ..

# 5. 转换模型
uv run python scripts/convert_to_gguf_local.py
# 输出：gguf_models_local/（4个文件，总计2-3秒）
```

</details>

<details>
<summary><b>方法二：Modal 云端（x86_64 + A10G）</b></summary>

```bash
# 1. 登录 Modal
uv run modal setup

# 2. 运行转换
uv run modal run scripts/convert_to_gguf_simple.py
# 耗时约5-8分钟（包括 llama.cpp 编译）

# 3. 下载模型
mkdir -p gguf_models
uv run modal volume get browser-control-fine-tune-with-grpo \
  gguf_output gguf_models/
```

</details>

### 阶段五：评估

```bash
# 在训练的模型上运行评估
make evaluation

# 或手动指定检查点
uv run python -m browser_control.evaluate \
  --checkpoint ./checkpoints/LFM2-350M-browsergym-20260220-182152
```

---

## 📚 核心概念

### GRPO 算法

**定义**: 组相对策略优化 - 一种内存高效的强化学习算法

**工作原理**:
- 将多个 rollout 分组
- 在组内比较性能
- 优于平均 → 正优势
- 劣于平均 → 负优势
- **优势**: 不需要价值网络（相比 PPO）

**参考**: TRL 库（`trl.GRPOTrainer`）

### BrowserGym 环境

**目的**: 网页自动化的标准化强化学习环境

**组件**:
- **任务**: MiniWoB 基准测试（点击、输入、导航）
- **观察**: DOM 树或 AXTree（可访问性树）
- **动作**: 浏览器交互（点击、输入、滚动）
- **奖励**: 任务完成信号

**构建**: HuggingFace Space（远程执行）

### Modal 基础设施

**目的**: 无服务器 GPU 执行平台

**资源**:
- **存储卷**: 持久化存储
  - `browser-control-fine-tune-with-grpo`: 模型检查点
  - `hf-model-cache`: HuggingFace 模型缓存
- **密钥**: 环境变量
  - `wandb-secret`: WandB API 密钥
- **GPU**: A100（训练），A10G（转换）

### GGUF 格式

**目的**: 用于移动/边缘推理的高效模型格式

**特性**:
- 内存映射文件格式
- 多种量化级别（Q4_K_M 到 FP16）
- 兼容 llama.cpp 生态系统
- 被 LeapSDK 使用（Android/iOS）

**转换**: HuggingFace → FP16 GGUF → 量化 GGUF

---

## 🔧 常见问题与解决方案

### 问题一：SOCKS 代理 + httpx

**症状**: `httpx` 初始化失败
**修复**: `uv pip install httpx[socks]`

### 问题二：本地 CUDA不可用

**症状**: `torch.cuda.is_available() == False`
**诊断**:
1. 检查 CUDA 版本: `nvidia-smi`（必须是 13.0）
2. 检查 PyTorch: `python -c "import torch; print(torch.__version__)"` (应显示 `+cu130`)
3. 检查 pyproject.toml: 验证 pytorch-cu130 索引配置

**修复**: 详细步骤见 `docs/browser-control-android-deploy.md`

### 问题三：Modal Volume 未找到

**症状**: `modal volume ls` 返回空或错误
**修复**: 确保训练成功完成并保存了检查点

### 问题四：BrowserGym 连接超时

**症状**: 评估挂起或超时
**诊断**: 检查 HF Space 状态: https://huggingface.co/spaces/burtenshaw-browsergym-v2
**修复**: 等待 space 重启，或在 HF Space 讨论区报告问题

---

## 📖 文档索引

### 主要文档（面向开发者）
- **AGENTS.md**（本文件）: AI 代理开发指南
- **SKILL.md**: 项目技能与技术
- **README.md**: 面向用户的项目概览

### 构建指南
- **docs/browser-control-model-deploy.md**: 训练构建（阶段 1-5）
- **docs/browser-control-android-deploy.md**: Android 构建计划（6 个阶段）

### 参考资料
- **configs/*.yaml**: 训练配置示例
- **Makefile**: 常用命令
- **pyproject.toml**: 依赖规范

---

## 🎓 学习资源

### 内部资源
- 模型训练日志: WandB 项目 `browser-control-fine-tune-with-grpo`
- 评估结果: `media/` 目录（截图）

### 外部资源
- **Liquid AI 文档**: https://docs.liquid.ai/examples/laptop-examples/browser-control
- **TRL (GRPO)**: https://huggingface.co/docs/trl/
- **BrowserGym**: https://github.com/ServiceNow/BrowserGym
- **Modal**: https://modal.com/docs
- **llama.cpp**: https://github.com/ggerganov/llama.cpp
- **LeapSDK**: https://github.com/Liquid4All/LeapSDK-Examples

---

## 🤖 AI 代理指南

### 在此项目上工作时

**应该做**:
- 开始任务前阅读本文件和相关文档
- 对架构和工作流程提出明确问题
- 参考现有配置和脚本作为模板
- 验证更改不会破坏现有功能
- 构建到 Modal 前先本地测试

**不应该做**:
- 在不理解 GRPO 原理的情况下修改核心算法
- 在未测试的情况下更改 Modal 基础设施
- 忽略 pyproject.toml 依赖规范
- 跳过新功能的文档更新
- 在用户使用 ARM64 系统时假定为 x86_64

### 常见任务模式

**训练任务**:
1. 验证 Modal 凭据
2. 选择合适的配置（debug 用于测试，full 用于生产）
3. 运行训练命令
4. 监控 WandB 日志
5. 从 Modal volume 下载检查点

**转换任务**:
1. 检查系统架构（`uname -m`）
2. 选择方法（ARM64+CUDA13 用本地，其他用 Modal）
3. 运行转换脚本
4. 验证 GGUF 文件（4 个量化级别）
5. 使用 llama-cli 测试

**调试任务**:
1. 检查相关文档部分
2. 验证环境设置（uv sync、CUDA、Modal）
3. 检查错误信息和日志
4. 在项目历史中搜索类似问题
5. 如果是新问题，记录解决方案

---

## 📝 版本历史

| 日期 | 版本 | 变更 |
|------|---------|---------|
| 2026-02-22 | 1.0 | 初始创建 AGENTS.md |
| 2026-02-21/22 | - | 阶段一模型转换完成（2 种方法）|
| 2026-02-20 | - | 初始训练管道验证（debug 模式）|

---

**有问题？** 查看 `docs/` 中的文档或搜索项目问题。

**贡献代码？** 遵循本文件中的指南并先在本地测试更改。
