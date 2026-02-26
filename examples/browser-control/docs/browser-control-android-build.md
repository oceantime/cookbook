# 在 Android 上构建 Browser Control 演示应用

本文档描述如何将微调后的 LFM2-350M（GGUF 格式）集成到 Android 应用中，实现设备端浏览器控制。

## 前置条件

- Android Studio（Hedgehog 或更高版本）
- Android SDK API 26+
- NDK 27+
- 已量化的 GGUF 模型文件（参见 `docs/browser-control-model-build.md`）

## 项目结构

```
android/BrowserControlDemo/
├── app/
│   ├── src/main/
│   │   ├── java/ai/liquid/browsercontrol/
│   │   │   ├── MainActivity.kt
│   │   │   ├── LlmInference.kt     # LEAP SDK 封装
│   │   │   └── BrowserAgent.kt     # 浏览器控制逻辑
│   │   └── res/
│   └── build.gradle.kts
├── build.gradle.kts
└── settings.gradle.kts
```

## 构建步骤

### 1. 准备模型

将量化好的 GGUF 文件放入 `android/BrowserControlDemo/app/src/main/assets/`:

```
assets/
└── lfm2-350m-browsergym-q4_k_m.gguf
```

### 2. 集成 LEAP SDK

在 `build.gradle.kts` 中添加依赖：

```kotlin
dependencies {
    implementation("ai.liquid:leap-android:1.0.0")
}
```

### 3. 构建 APK

```bash
cd android/BrowserControlDemo
./gradlew assembleDebug
```

### 4. 安装到设备

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## 关键 API

```kotlin
// 初始化 LLM
val llm = LlmInference.createFromFile(context, modelPath)

// 执行浏览器控制推理
val action = llm.generateResponse(prompt)
// 返回格式: click('13') / fill('42', 'text') / noop()
```

## 注意事项

- 模型文件较大（~200MB），建议通过网络下载而非打包进 APK
- 首次推理可能需要 2-5 秒预热
- 建议在后台线程运行推理以避免 ANR
- LEAP SDK 支持 ARM64-v8a（大多数现代 Android 设备）
