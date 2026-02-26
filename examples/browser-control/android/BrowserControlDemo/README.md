# 构建说明

本目录包含 BrowserControlDemo Android 应用骨架。

## 前置条件

- Android Studio Hedgehog 或更高版本
- Android SDK API 26+
- NDK r27+（如需启用 LEAP SDK 本地推理）

## 构建步骤

### 1. 准备模型（可选，启用真实推理时需要）

将量化后的 GGUF 模型放入 `app/src/main/assets/`：

```bash
cp ../../gguf_models_local/LFM2-350M-browsergym-q4_k_m.gguf \
   app/src/main/assets/model.gguf
```

### 2. 启用 LEAP SDK（可选）

在 `app/build.gradle.kts` 中取消注释：

```kotlin
implementation("ai.liquid:leap-android:1.0.0")
```

然后在 `BrowserAgent.kt` 中取消 TODO 注释。

### 3. 构建 APK

```bash
./gradlew assembleDebug
```

APK 输出路径：`app/build/outputs/apk/debug/app-debug.apk`

### 4. 安装到设备

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## 当前状态

- **Demo 模式**（默认）：使用简单启发式规则模拟推理，无需模型文件
- **真实推理模式**：需要 LEAP SDK + GGUF 模型文件
