# LeapSDK 本地模型加载工作流

> **适用范围**: 本项目（BrowserControlDemo）  
> **标签**: leapsdk, android, model-loading, gguf, offline

---

## LeapDownloader 识别模型所需文件

`downloader.queryStatus()` 返回 `Downloaded` 需要同时存在**两个文件**：

```
/data/user/0/<pkg>/files/leap_models/<MODEL>-<QUANT>/
├── <MODEL>-<QUANT>.gguf   ← 模型权重（LFM2-350M-Q8_0 为 ~361MB）
└── <MODEL>-<QUANT>.json   ← metadata（约 1.8KB，必须！）
```

**只有 GGUF 没有 JSON → `queryStatus()` 仍返回 `NotOnLocal`。**

---

## 模型文件信息

| 文件 | 大小 | 来源 |
|------|------|------|
| `LFM2-350M-Q8_0.gguf` | ~361 MB | HuggingFace / 本地 |
| `LFM2-350M-Q8_0.json` | ~1.8 KB | `https://huggingface.co/LiquidAI/LeapBundles/resolve/main/LFM2-350M-GGUF/Q8_0.json` |

**项目根目录已包含 `LFM2-350M-Q8_0.json`，无需每次下载。**

---

## 模拟器/离线构建完整流程

模拟器通常无法访问 HuggingFace，需要手动推送两个文件：

```bash
# 步骤 1: 推送到 sdcard 中转
adb push LFM2-350M-Q8_0.gguf /sdcard/LFM2-350M-Q8_0.gguf
adb push LFM2-350M-Q8_0.json /sdcard/LFM2-350M-Q8_0.json

# 步骤 2: 创建内部缓存目录（以 app 身份）
adb shell "run-as ai.liquid.browsercontrol mkdir -p files/leap_models/LFM2-350M-Q8_0"

# 步骤 3: 复制（SELinux context 自动正确）
adb shell "run-as ai.liquid.browsercontrol cp /sdcard/LFM2-350M-Q8_0.gguf files/leap_models/LFM2-350M-Q8_0/LFM2-350M-Q8_0.gguf"
adb shell "run-as ai.liquid.browsercontrol cp /sdcard/LFM2-350M-Q8_0.json files/leap_models/LFM2-350M-Q8_0/LFM2-350M-Q8_0.json"

# 步骤 4: 验证
adb shell "run-as ai.liquid.browsercontrol ls -la files/leap_models/LFM2-350M-Q8_0/"
```

预期输出：
```
-rw------- u0_a227 u0_a227 379XXXXXX LFM2-350M-Q8_0.gguf
-rw------- u0_a227 u0_a227      1800 LFM2-350M-Q8_0.json
```

---

## LeapSDK API 关键调用

```kotlin
// 正确的包路径（v0.9.7）
import ai.liquid.leap.*
import ai.liquid.leap.message.*
import ai.liquid.leap.downloader.*

// 检查状态（需要 GGUF + JSON 都存在）
val status = downloader.queryStatus(modelName, quantizationType)

// 加载模型（参数名注意）
modelRunner = downloader.loadModel(
    modelName = "LFM2-350M",       // 不是 modelSlug
    quantizationType = "Q8_0"      // 不是 quantizationSlug
)

// 创建会话
conversation = modelRunner?.createConversation(systemPrompt)

// 流式推理
conversation.generateResponse(userPrompt).collect { response ->
    when (response) {
        is MessageResponse.Chunk -> emit(response.text)
        else -> { /* 忽略其他类型 */ }
        // 注意：Android SDK 没有 MessageResponse.Complete
    }
}
```

---

## 路径对照表

| 路径类型 | 值 |
|---------|-----|
| SDK 内部缓存 | `/data/user/0/ai.liquid.browsercontrol/files/leap_models/LFM2-350M-Q8_0/` |
| adb push 中转 | `/sdcard/LFM2-350M-Q8_0.gguf` |
| 外部镜像（adb push 直接目标，但有 SELinux 问题） | `/storage/emulated/0/Android/data/ai.liquid.browsercontrol/files/leap_models/LFM2-350M-Q8_0/` |

**结论：推荐走 `/sdcard` 中转 + `run-as cp` 路线，避免 SELinux 权限问题。**
