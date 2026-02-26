# Skill: 模型量化（GGUF）

**类别**: 模型构建 / 量化  
**适用场景**: 减小模型体积用于移动/边缘构建  
**创建时间**: 2026-02-22

---

## 量化方法对比

| 方法 | 精度 | 体积 | 质量 | 使用场景 |
|------|------|------|------|---------|
| FP16 | 16位浮点 | 基准（678MB）| 最佳 | 开发、基准测试 |
| Q8_0 | 8位 | 减小47%（362MB）| 高 | 生产环境（推荐）|
| Q5_K_M | 5位混合 | 减小63%（249MB）| 良好 | 平衡 |
| Q4_K_M | 4位混合 | 减小68%（219MB）| 可接受 | 低端设备 |

## 转换管道

```bash
# 步骤1: HuggingFace → FP16 GGUF
python llama.cpp/convert_hf_to_gguf.py \
  checkpoint_dir \
  --outfile model-fp16.gguf \
  --outtype f16

# 步骤2: FP16 → 量化
llama.cpp/build/bin/llama-quantize \
  model-fp16.gguf model-q8_0.gguf Q8_0

# 步骤3: 验证（本地推理测试）
llama.cpp/build/bin/llama-cli \
  -m model-q8_0.gguf \
  -p "测试提示" \
  -n 50
```

## 关键概念

- **K-quants**: 混合精度方案（Q5_K_M 使用5位并混合部分6位权重）
- **困惑度**: 量化后衡量质量损失的指标
- **内存映射**: GGUF 文件可使用 mmap 高效加载

## subprocess Unicode 处理

```python
# 问题: llama-quantize 输出非 UTF-8 进度条
# 解决: 忽略无效字符
result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
```

## 转换速度对比

| 环境 | 耗时 | 加速比 |
|------|------|--------|
| 本地 ARM64+CUDA13 | 2-3 秒 | 基准 |
| Modal x86_64+A10G | 5-8 分钟 | 1x（慢100-200倍）|

## 推理基准（llama.cpp，ARM64）

| 测试场景 | Prompt 处理 | 生成速度 | 备注 |
|----------|------------|---------|------|
| 旧基准（ARM64 CPU）| 167-487 t/s | 6-7 t/s | 早期测试 |
| run31 Q8_0（2026-02-26，ARM64 CPU）| 116.2 t/s | 15.2 t/s | llama-cli，CPU 模式，`-ngl 0` |

> 注：`llama-cli` 默认进入交互对话模式（等待 stdin），验证时加 `--simple-io` 可简化输出，
> 或改用 `-n <tokens>` 限制生成长度后用 `Ctrl+C` 中断。

## 工具

- llama.cpp: https://github.com/ggerganov/llama.cpp
- GGML 格式规范
- LeapSDK（移动推理）
