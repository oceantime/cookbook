# LeapSDK：替换微调模型（不换架构）

> **适用范围**: 本项目（BrowserControlDemo）  
> **标签**: leapsdk, gguf, model-swap, finetuned, adb

---

## 背景

同一 base 架构（LFM2-350M）的不同微调版本可以**只替换 .gguf 文件**，JSON manifest 不变，因为：
- `.gguf` 包含权重
- `.json` 包含架构元数据（词表大小、层数、上下文长度）—— 微调不改变架构

---

## 快速替换流程

```bash
# 1. 转换目标模型为 Q8_0 GGUF（参见 safetensors-to-gguf-pipeline.md）
llama.cpp/build/bin/llama-quantize \
    checkpoints/<new-model>-F16.gguf \
    checkpoints/<new-model>-Q8_0.gguf Q8_0

# 2. 覆盖设备上的 GGUF（JSON 不动）
adb push checkpoints/<new-model>-Q8_0.gguf /sdcard/LFM2-350M-Q8_0.gguf

# 3. 验证文件大小
adb shell ls -lh /sdcard/LFM2-350M-Q8_0.gguf
```

---

## 本项目两个可用模型

| 模型 | 来源 | 本地路径 | 说明 |
|------|------|---------|------|
| 自训练模型 | GRPO 10步 debug 训练 | `checkpoints/LFM2-350M-browsergym-20260220-182152/` | safetensors，需转换 |
| 作者模型 | `Paulescu/LFM2-350M-browsergym-20251224-013119` | `checkpoints/LFM2-350M-paulescu-Q8_0.gguf` | 已转换 ✅ |

**推送作者模型**：
```bash
adb push checkpoints/LFM2-350M-paulescu-Q8_0.gguf /sdcard/LFM2-350M-Q8_0.gguf
```

**恢复原模型**（先备份）：
```bash
adb shell cp /sdcard/LFM2-350M-Q8_0.gguf /sdcard/LFM2-350M-Q8_0.gguf.bak
adb push <original>.gguf /sdcard/LFM2-350M-Q8_0.gguf
```

---

## app 侧无需改动

`ModelInference.kt` 中 `LOCAL_GGUF_FILENAME = "LFM2-350M-Q8_0.gguf"` 固定写死，替换模型只需文件名对应即可，不需要重新编译 APK。

---

## 验证步骤

1. 在 app 点「**重置**」清除旧状态
2. 点「**加载模型**」— 日志应显示 `✓ 模型加载成功`
3. 点「**开始任务**」— 观察模型输出 `click('bid')` 是否正确
4. 看 WebView 覆盖层 reward 结果（绿色=成功）
