# LoRA 微调配置

## 背景
LoRA（Low-Rank Adaptation）通过在预训练模型的权重矩阵旁边添加小的可训练矩阵，显著减少训练参数量和显存占用，同时保持接近全量微调的效果。

## GRPO + LoRA 配置

```yaml
# 启用 LoRA
use_peft: true
lora_r: 8            # 秩（rank），越大表示越多参数
lora_alpha: 16       # 缩放系数（通常为 2×rank）
lora_dropout: 0.0    # Dropout（训练较短时设为 0）
lora_bias: "none"    # 是否训练 bias
use_rslora: false    # RSLoRA（秩稳定 LoRA）

# 目标模块（LFM2 的 attention 和 FFN 层）
lora_target_modules:
  - "q_proj"
  - "k_proj"
  - "v_proj"
  - "o_proj"
  - "gate_proj"
  - "up_proj"
  - "down_proj"

# LoRA 适合更高学习率
learning_rate: 1.0e-4   # LoRA: 1e-4（全量微调: 5e-6）
```

## 参数量对比（LFM2-350M）

| 方案 | 可训练参数 | 显存占用 |
|------|---------|---------|
| 全量微调 | ~350M | ~28GB |
| LoRA r=8 | ~3.5M (~1%) | ~8GB |
| LoRA r=16 | ~7M (~2%) | ~10GB |

## 保存与合并

```python
# 保存 LoRA adapter
trainer.model.save_pretrained("checkpoints/lora-adapter")

# 合并到基础模型（用于推理/量化）
from peft import PeftModel
from transformers import AutoModelForCausalLM

base_model = AutoModelForCausalLM.from_pretrained("LiquidAI/LFM2-350M")
model = PeftModel.from_pretrained(base_model, "checkpoints/lora-adapter")
merged = model.merge_and_unload()
merged.save_pretrained("checkpoints/merged-model")
```

## 注意事项
- LoRA 只保存 adapter 权重（几 MB），推理时需要原始基础模型
- GGUF 量化前需要先合并（merge_and_unload）
- `use_rslora: true` 在高秩（r≥16）时更稳定
