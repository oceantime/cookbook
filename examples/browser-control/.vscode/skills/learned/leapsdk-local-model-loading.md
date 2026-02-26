# LEAP SDK 本地模型加载

## 背景
LEAP SDK 是 Liquid AI 提供的推理 SDK，支持在 Android/iOS 设备上本地运行 LFM 模型（GGUF 格式）。

## 模型格式要求
- 必须转换为 GGUF 格式（Q4_K_M 量化适合移动端）
- 模型文件命名建议：`lfm2-350m-browsergym-q4_k_m.gguf`

## Android 集成

### 依赖
```kotlin
// build.gradle.kts
dependencies {
    implementation("ai.liquid:leap-android:1.0.0")
}
```

### 初始化
```kotlin
import ai.liquid.leap.LlmInference

val modelPath = context.getExternalFilesDir(null)?.absolutePath + "/model.gguf"
val llm = LlmInference.createFromFile(context, modelPath)
```

### 推理
```kotlin
val prompt = buildPrompt(systemPrompt, domContent, userGoal)
val response = llm.generateResponse(prompt)
// response: "click('13')" 或 "fill('42', 'hello')" 等
```

## GGUF 转换
```bash
# 本地转换（需要 llama.cpp）
python scripts/convert_to_gguf_local.py \
  --model-path checkpoints/<experiment-name> \
  --output-path gguf_models_local/

# Modal 云端转换
uv run modal run -m src.browser_control.convert_to_gguf_modal
```

## 注意事项
- LEAP SDK 目前支持 ARM64-v8a 架构
- 量化精度 Q4_K_M 在速度和质量间取得平衡
- 首次加载模型需要 2-5 秒
- 推理建议在 `Dispatchers.IO` 协程中运行
