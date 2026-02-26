# Android 浏览器控制示例

## 背景
将微调后的 LFM2-350M（GGUF 格式）集成到 Android 应用，通过 LEAP SDK 实现设备端网页任务自动化。

## 项目结构
```
android/BrowserControlDemo/
├── app/
│   ├── src/main/
│   │   ├── java/ai/liquid/browsercontrol/
│   │   │   ├── MainActivity.kt
│   │   │   ├── LlmInference.kt
│   │   │   └── BrowserAgent.kt
│   │   ├── res/layout/activity_main.xml
│   │   └── AndroidManifest.xml
│   └── build.gradle.kts
├── build.gradle.kts
└── settings.gradle.kts
```

## 核心代码

```kotlin
// BrowserAgent.kt
class BrowserAgent(context: Context, modelPath: String) {
    private val llm = LlmInference.createFromFile(context, modelPath)

    suspend fun executeStep(domContent: String, goal: String): String {
        val prompt = """
            |${SYSTEM_PROMPT}
            |Goal: $goal
            |Current page:
            |$domContent
        """.trimMargin()

        return withContext(Dispatchers.IO) {
            llm.generateResponse(prompt)
        }
    }

    companion object {
        const val SYSTEM_PROMPT = """
            You control a web browser through BrowserGym actions.
            Reply with exactly ONE action on a single line.
        """
    }
}
```

## 构建要求
- Android Studio Hedgehog+
- Android SDK API 26+
- NDK r27+
- LEAP SDK `ai.liquid:leap-android:1.0.0`

## 模型部署方式

### 方案 1：Assets 打包（小模型）
```
app/src/main/assets/lfm2-350m-q4_k_m.gguf
```

### 方案 2：运行时下载（推荐）
```kotlin
// 首次启动时从服务器下载
val modelUrl = "https://your-cdn.com/lfm2-350m-q4_k_m.gguf"
val localPath = context.getExternalFilesDir(null)?.absolutePath + "/model.gguf"
downloadModel(modelUrl, localPath)
```

## 权限要求
```xml
<!-- AndroidManifest.xml -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
```

## 注意事项
- Q4_K_M 量化文件约 200MB，建议网络下载
- 模型推理需在 IO 线程运行
- 建议在 Android 12+ 设备测试（更好的内存管理）
