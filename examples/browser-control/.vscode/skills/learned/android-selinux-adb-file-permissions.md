# Android SELinux adb 文件权限问题

> **适用范围**: Android 开发（跨项目通用）  
> **标签**: android, adb, selinux, permissions, internal-storage

---

## 问题现象

通过 `adb push` 或 Android Studio Device Explorer 推送到 app 内部存储的文件，app 进程无法访问：

- `File.exists()` → `false`
- `File.listFiles()` → `null` 或空数组
- 目录本身存在（`drwxrwxrwx u0_a227`）但文件不可见
- logcat 无报错，表现为"文件不存在"

## 根本原因

**SELinux 强制访问控制**。`adb push` 和 Device Explorer 以 `shell` 用户身份写入文件，文件的：
- 所有者：`shell:shell`
- SELinux context：`shell_data_file`

App 进程的 SELinux domain 是 `untrusted_app`，无法访问 `shell_data_file` context 的文件，即使文件系统权限位（rwx）看起来允许。

---

## 解决方案：用 `run-as` 以 app 身份复制

```bash
# 1. 推送文件到 sdcard 中转（shell 可写，任何人可读）
adb push <file> /sdcard/<file>

# 2. 创建目标目录（以 app 用户身份）
adb shell "run-as <package.name> mkdir -p files/<relative/path>"

# 3. 复制到内部存储（文件归属自动变为 app 用户）
adb shell "run-as <package.name> cp /sdcard/<file> files/<relative/path>/<file>"

# 4. 验证（归属应为 u0_aXXX，不是 shell）
adb shell "run-as <package.name> ls -la files/<relative/path>/"
```

### 实际示例（本项目）

```bash
adb push LFM2-350M-Q8_0.gguf /sdcard/LFM2-350M-Q8_0.gguf
adb shell "run-as ai.liquid.browsercontrol mkdir -p files/leap_models/LFM2-350M-Q8_0"
adb shell "run-as ai.liquid.browsercontrol cp /sdcard/LFM2-350M-Q8_0.gguf files/leap_models/LFM2-350M-Q8_0/LFM2-350M-Q8_0.gguf"
adb shell "run-as ai.liquid.browsercontrol ls -la files/leap_models/LFM2-350M-Q8_0/"
# 预期输出：-rw------- u0_a227 u0_a227 379XXXXXX LFM2-350M-Q8_0.gguf
```

### 前提条件
- App 必须是 **debuggable**（`android:debuggable="true"` 或 debug build）
- `run-as` 在 userdebug/eng 系统镜像上有效，user 版本 release 设备可能受限

---

## 代码层面：不要依赖 listFiles()

```kotlin
// ❌ 不可靠 — listFiles() 对 shell 写入的文件返回 null
val file = dir.listFiles()?.firstOrNull { it.extension == "gguf" }

// ✅ 可靠 — 直接按已知文件名检查（exists() 语义不同于 listFiles()）
val file = File(dir, "model.gguf").takeIf { it.exists() && it.length() > 0 }
```

> **注意**：即使 `exists()` 在 SELinux 阻断时也可能返回 false（取决于 Android 版本）。  
> 根本解决是用 `run-as` 确保文件归属正确。

---

## 为什么 exists() 有时也失败

SELinux 的访问控制发生在 syscall 层。`exists()` 底层调用 `stat()`，`listFiles()` 调用 `getdents()`，两者都受 SELinux 约束。区别在于某些 Android 版本对目录的 `execute` 位检查不同。

---

## 参考
- Android docs: [App-specific files](https://developer.android.com/training/data-storage/app-specific)
- SELinux for Android: [source.android.com/docs/security/features/selinux](https://source.android.com/docs/security/features/selinux)
