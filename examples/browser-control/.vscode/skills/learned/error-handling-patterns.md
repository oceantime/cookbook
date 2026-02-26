# Skill: 常见错误处理模式

**类别**: 调试 / 错误处理  
**适用场景**: browser-control 训练和构建中常见错误的处理方式  
**创建时间**: 2026-02-22

---

## 1. subprocess Unicode 错误

**问题**: `llama-quantize` 输出非 UTF-8 的进度条

```python
result = subprocess.run(cmd, capture_output=True, text=True)
# UnicodeDecodeError!
```

**解决**:

```python
result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
```

---

## 2. Modal Volume 并发写入

**问题**: 多次写入后未 commit，导致数据丢失

```python
# 错误方式：忘记 commit
volume.put_file("file1.txt", "/remote/path1")
# 数据可能丢失！
```

**解决**:

```python
# 方式1: 手动 commit
volume.put_file("file1.txt", "/remote/path1")
volume.commit()

# 方式2: batch_upload 上下文管理器（自动 commit）
with volume.batch_upload() as batch:
    batch.put_file("file1.txt", "/remote/path1")
    batch.put_file("file2.txt", "/remote/path2")
```

---

## 3. BrowserGym HF Space 休眠

**问题**: HuggingFace Space 长时间不活跃后进入休眠

```python
# 连接超时
env = BrowserGymEnv(...)  # ConnectionError!
```

**解决**:

```python
import time

try:
    env = BrowserGymEnv(...)
except ConnectionError:
    print("Waiting for HF Space to wake up...")
    time.sleep(30)
    env = BrowserGymEnv(...)  # 重试
```

---

## 4. Kotlin K2 编译器 FIR 崩溃

**问题**: 第三方 SDK 使用较新 Kotlin 编译，K2 编译器检测到版本不兼容时内部崩溃

```
FileAnalysisException: source must not be null
at FirIncompatibleClassExpressionChecker.checkSourceElement
```

**解决** （`app/build.gradle.kts`）:

```kotlin
kotlinOptions {
    jvmTarget = "17"
    freeCompilerArgs += listOf("-Xskip-metadata-version-check")
}
```

---

## 5. Android 构建版本不兼容

**问题**: Java/Gradle/AGP/SDK 版本不匹配导致构建失败

**解决**: 按版本兼容性矩阵升级，详见 `.vscode/skills/learned/android-build-compatibility.md`
---

## 6. unsloth GGUF 导出失败（Modal / Docker 环境）

**问题**: 在 Modal 或 Docker 中调用 `model.save_pretrained_gguf()` 报错

```
RuntimeError: llama.cpp folder 'llama.cpp' does not exist in /root
```

或：
```
[FAIL] Command `uv pip install gguf protobuf` failed: error: No virtual environment found
```

**根本原因**: unsloth 的 GGUF 导出是对 llama.cpp 的封装，依赖特定路径和 Python 环境，在容器内难以满足。

**解决**: 跳过 unsloth，**直接使用 llama.cpp 工具链**：

```bash
# Step 1: safetensors → F16 GGUF
python llama.cpp/convert_hf_to_gguf.py checkpoint_dir \
    --outfile model-f16.gguf --outtype f16

# Step 2: 量化
llama.cpp/build/bin/llama-quantize model-f16.gguf model-q8_0.gguf Q8_0
```

优势：减少依赖层次，错误易定位，适用于任何环境（本地/Modal/Docker）。