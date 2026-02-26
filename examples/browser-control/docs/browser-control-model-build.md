# 在 Modal 上构建 Browser Control 模型

本文档描述如何使用 Modal 平台对 LFM2-350M 进行 GRPO 微调（云端构建）。

## 前置条件

1. 安装 `uv` 和 `modal`
2. 配置 Modal secrets（`wandb-secret`、HuggingFace token）
3. 确保 `configs/` 目录下有所需的 YAML 配置文件

## 构建步骤

### 1. 安装依赖

```bash
uv sync
```

### 2. 选择配置

| 配置文件 | 说明 |
|---------|------|
| `configs/lfm2_350m.yaml` | 全量微调（Modal A100） |
| `configs/lfm2_350m_lora.yaml` | LoRA 微调（Modal A100，省显存） |

### 3. 运行微调

```bash
make fine-tune config=lfm2_350m.yaml
# 或
make fine-tune config=lfm2_350m_lora.yaml
```

等价于：

```bash
uv run modal run -m src.browser_control.fine_tune --config-file-name lfm2_350m.yaml
```

### 4. 监控训练

- WandB 项目：`browser-control-fine-tune-with-grpo`
- Modal 面板：https://modal.com/apps

## 关键参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `model_name` | HuggingFace 模型名 | `LiquidAI/LFM2-350M` |
| `max_steps` | 每次 rollout 最大步数 | 10 |
| `num_generations` | 每个 prompt 生成的候选数 | 4 |
| `use_vllm` | 使用 vLLM 加速推理 | true |
| `vllm_mode` | vLLM 模式 | `colocate` |

## GGUF 量化（构建后）

微调完成后，使用以下命令将模型量化为 GGUF 格式以便本地推理：

```bash
uv run modal run -m src.browser_control.convert_to_gguf_modal
```

或在本地（需要 llama.cpp）：

```bash
python scripts/convert_to_gguf_local.py --model-path checkpoints/<experiment-name>
```
