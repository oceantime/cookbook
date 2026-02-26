# 模型量化为 GGUF 格式

## 背景
GGUF 是 llama.cpp 使用的量化模型格式，支持 CPU/GPU 混合推理，适合在边缘设备（手机、PC）上运行。

## 量化方案对比

| 方案 | 大小 | 质量 | 适用场景 |
|------|------|------|---------|
| Q8_0 | ~350MB | 接近原始 | 高端手机 / PC |
| Q4_K_M | ~200MB | 良好 | 主流手机（推荐） |
| Q4_0 | ~185MB | 中等 | 低端设备 |
| Q2_K | ~130MB | 较低 | 极低内存设备 |

## 本地转换（llama.cpp）

### 前置条件
```bash
# 克隆并构建 llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make -j4
```

### 执行转换
```bash
python scripts/convert_to_gguf_local.py \
  --model-path checkpoints/<experiment-name> \
  --output-path gguf_models_local/ \
  --quantization Q4_K_M
```

或使用简化脚本：
```bash
python scripts/convert_to_gguf_simple.py checkpoints/<experiment-name>
```

## Modal 云端转换

```bash
uv run modal run -m src.browser_control.convert_to_gguf_modal \
  --checkpoint-name <experiment-name>
```

输出保存到 Modal Volume `browser-control-gguf-models`。

## llama.cpp 目录
项目根目录下的 `llama.cpp/` 是本地克隆，已加入 `.gitignore`，不提交。

## 注意事项
- HuggingFace Safetensors 格式需要先用 `convert_hf_to_gguf.py` 转换
- LFM2 使用自定义架构，确保使用支持 LFM2 的 llama.cpp 版本
- 量化前确保模型已完整保存（含 `config.json`、`tokenizer.json`）
