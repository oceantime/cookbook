# Android LLM 推理线程模型

> **适用范围**: Android LLM / AI 推理 app（跨项目通用）  
> **标签**: android, coroutines, threading, dispatchers, webview, llm

---

## 问题现象

加载模型或运行推理后 UI 完全卡顿、无响应、动画停止。

## 根本原因

`viewModelScope.launch {}` 默认使用 `Dispatchers.Main`（主线程）。  
LLM 推理是 CPU 密集型操作，在主线程运行会阻塞 UI 渲染。

---

## 解决方案

### 线程分配规则

| 操作类型 | 调度器 | 原因 |
|---------|--------|------|
| LLM 推理 / 模型加载 | `Dispatchers.Default` | CPU 密集，多核并行 |
| 大文件复制（GGUF 361MB） | `Dispatchers.IO` | 阻塞 IO |
| 网络请求（下载 JSON manifest） | `Dispatchers.IO` | 阻塞 IO |
| `WebView.evaluateJavascript()` | `Dispatchers.Main` | **必须**，WebView 是 UI 组件 |
| `StateFlow.value = ...` 更新 | 任意线程 | StateFlow 线程安全 |

### ViewModel 模板

```kotlin
// 模型加载 — 在后台线程
fun loadModel() {
    viewModelScope.launch(Dispatchers.Default) {
        modelInference.loadModel(...)
        _modelState.value = ModelState.Ready  // StateFlow 线程安全
    }
}

// 推理任务循环
fun runTask(webView: WebView) {
    viewModelScope.launch(Dispatchers.Default) {
        // ✅ WebView JS 注入必须切回主线程
        val axtree = withContext(Dispatchers.Main) {
            WebViewAccessibility.extractAXTree(webView)
        }

        // ✅ 推理在后台线程（已在 Dispatchers.Default）
        val response = StringBuilder()
        modelInference.generateAction(prompt).collect { chunk ->
            response.append(chunk)
        }

        // ✅ WebView 动作执行必须切回主线程
        val result = withContext(Dispatchers.Main) {
            ActionExecutor.execute(webView, action)
        }
    }
}
```

### Flow 推理

```kotlin
fun generateAction(prompt: String): Flow<String> = flow {
    conversation.generateResponse(prompt).collect { response ->
        if (response is MessageResponse.Chunk) emit(response.text)
    }
}.flowOn(Dispatchers.Default)  // ← 关键：确保在后台线程执行
```

### 文件 IO

```kotlin
private suspend fun copyLargeFile(src: File, dst: File) {
    withContext(Dispatchers.IO) {  // 大文件复制用 IO dispatcher
        src.copyTo(dst, overwrite = true)
    }
}
```

---

## 常见错误

```
CalledFromWrongThreadException: Only the original thread that created a view hierarchy can touch its views.
```
→ `WebView.evaluateJavascript()` 在非主线程调用，需加 `withContext(Dispatchers.Main)`。

---

## 进阶：避免长时间阻塞 Default dispatcher

LFM2-350M Q8_0 在模拟器上推理可能耗时 30-120 秒，`Dispatchers.Default` 线程池有限，注意不要用 `Dispatchers.Default` 执行阻塞 IO（用 `Dispatchers.IO`）。
