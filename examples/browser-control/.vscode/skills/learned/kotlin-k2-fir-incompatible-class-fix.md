# Skill: Kotlin K2 编译器 FIR 崩溃修复

**类别**: Android 开发 / Kotlin 编译器  
**适用场景**: 使用第三方 SDK（如 LeapSDK）时 Kotlin K2 编译器内部崩溃  
**创建时间**: 2026-02-22

---

## 问题现象

```
org.jetbrains.kotlin.util.FileAnalysisException: While analysing MainActivity.kt:24:5
java.lang.IllegalArgumentException: source must not be null
    at FirIncompatibleClassExpressionChecker.checkSourceElement
    at FirIncompatibleClassTypeChecker.check
```

---

## 根本原因

这是 Kotlin K2 编译器的已知 bug：

1. 第三方库（如 LeapSDK）使用了**较新版本的 Kotlin** 编译
2. K2 编译器的 `FirIncompatibleClassExpressionChecker` 检测到版本不兼容
3. 编译器尝试上报错误时，库中**合成代码没有源码位置**（source = null）
4. 导致 `requireNotNull` 抛出 `IllegalArgumentException` 崩溃

---

## 解决方案

在 `app/build.gradle.kts` 中添加编译参数跳过元数据版本检查：

```kotlin
// app/build.gradle.kts
android {
    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf("-Xskip-metadata-version-check")
    }
}
```

---

## 替代方案（降级 Kotlin）

如果不想跳过检查，也可以将 Kotlin 版本降级到与 SDK 兼容的版本：

```kotlin
// build.gradle.kts (project)
plugins {
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
}
```

---

## 注意事项

- `-Xskip-metadata-version-check` 会**跳过所有**元数据版本检查
- 实际兼容性风险通常很低（SDK 通常向后兼容）
- 升级 SDK 到最新版本后可以移除此参数
- 此参数不影响代码运行时行为，仅影响编译时检查

---

## 触发此问题的已知库

- `ai.liquid.leap:leap-sdk` （LeapSDK）
- 其他使用较新 Kotlin 编译的私有 SDK
