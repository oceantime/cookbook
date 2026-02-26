# Browser Control Agent Rules

## 项目简介
本项目基于 BrowserGym + GRPO 对 LFM2-350M 进行微调，使其具备网页操作能力。

## 工作流程

### 本地构建环境（DGX / GPU 服务器）
- 使用 Docker 隔离训练依赖
- `docker/training/` — 训练镜像
- `docker/browsergym/` — BrowserGym 环境镜像
- `docker/miniwob/` — MiniWoB++ 任务镜像
- 训练日志写入 `docker/logs/`（TensorBoard 格式，不提交）
- 训练权重保存至 `checkpoints/`（不提交）

### 云端构建（Modal）
- `src/browser_control/fine_tune.py` — 使用 Modal 运行 GRPO 微调
- `src/browser_control/modal_infra.py` — Modal 基础设施配置
- `Makefile` 提供 `fine-tune` 和 `evaluation` 命令

### 模型量化（GGUF）
- `scripts/convert_to_gguf_local.py` — 本地使用 llama.cpp 转换 GGUF
- `scripts/convert_to_gguf_simple.py` — 简化版本地 GGUF 转换
- `src/browser_control/convert_to_gguf_modal.py` — Modal 云端 GGUF 转换

### 本地推理
- `configs/lfm2_350m_local.yaml` — 本地 GPU 全量微调配置
- `configs/lfm2_350m_local_full.yaml` — 本地 GPU 全量微调（大 batch）
- `configs/lfm2_350m_local_lora.yaml` — 本地 GPU LoRA 微调配置

## 文件命名规范
- 所有文档使用"构建"而非"部署"
- 技能文件保存在 `.vscode/skills/learned/`

## 不提交的文件
- `.env` — API 密钥
- `checkpoints/` — 模型权重
- `docker/logs/` — TensorBoard 日志（root 权限）
- `docker/*/OpenEnv/` — 克隆的外部仓库
- `llama.cpp/` — llama.cpp 源码
- `gguf_models/`、`gguf_models_local/` — 量化模型

## 技能查询
使用 `/skills <关键词>` 查询已学习的技能。详见 `SKILL.md`。
