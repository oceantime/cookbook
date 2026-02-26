# Skill: Android 构建版本兼容性链

**类别**: Android 开发  
**适用场景**: Android 项目构建失败，版本不兼容错误  
**创建时间**: 2026-02-22

---

## 问题背景

Android 项目构建系统存在严格的版本依赖链，升级任何一环都可能触发连锁错误：
- `AAR metadata: requires compileSdk XX or later`
- `requires Android Gradle plugin X.X.X or higher`
- `incompatible Java X and Gradle X`
- `Class was compiled with an incompatible version of Kotlin`

---

## 版本兼容性矩阵

### Java ↔ Gradle

| Java 版本 | 最低 Gradle 版本 |
|-----------|----------------|
| Java 17   | Gradle 7.3+    |
| Java 19   | Gradle 8.2+    |
| Java 21   | Gradle 8.5+    |

### AGP ↔ Gradle ↔ compileSdk

| AGP 版本 | 最低 Gradle | 最大推荐 compileSdk |
|----------|------------|-------------------|
| 8.2.2    | 8.2        | 34                |
| 8.7.3    | 8.5        | 35                |
| 8.9.1    | 8.5        | 36                |

### AndroidX 库 ↔ 最低要求

| 依赖库                       | 最低 AGP    | 最低 compileSdk |
|-----------------------------|------------|----------------|
| core-ktx:1.17.0             | 8.9.1      | 36             |
| core:1.17.0                 | 8.9.1      | 36             |
| work-runtime:2.10.0         | 8.7.3      | 35             |
| work-runtime-ktx:2.10.0     | 8.7.3      | 35             |

### Kotlin 版本 ↔ Compose

| Kotlin 版本 | Compose 方式                           |
|------------|---------------------------------------|
| < 2.0      | `composeOptions { kotlinCompilerExtensionVersion }` |
| >= 2.0     | `org.jetbrains.kotlin.plugin.compose` 插件 |

---

## 推荐版本组合（2026-02）

```kotlin
// build.gradle.kts (project)
plugins {
    id("com.android.application") version "8.9.1" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
}

// gradle/wrapper/gradle-wrapper.properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.11.1-bin.zip

// app/build.gradle.kts
android {
    compileSdk = 36
    defaultConfig {
        targetSdk = 35
        minSdk = 31
    }
    // Kotlin 2.0+ 不再需要 composeOptions 块！
}
```

---

## 升级步骤

当遇到版本不兼容时，按以下顺序升级：

1. **确认 Java 版本**: `java -version`
2. **升级 Gradle** 到与 Java 兼容的版本（`gradle-wrapper.properties`）
3. **升级 AGP** 到支持目标 SDK 的版本（`build.gradle.kts`）
4. **升级 Kotlin** 到与 stdlib 兼容的版本
5. **更新 compileSdk/targetSdk**（`app/build.gradle.kts`）
6. **迁移 Compose 插件**（Kotlin 2.0+ 移除 `composeOptions`）

---

## 清理缓存

版本升级后必须清理缓存：

```bash
# Windows
gradlew --stop
gradlew clean
rmdir /s /q .gradle
rmdir /s /q app\build

# Android Studio
# File → Invalidate Caches → Invalidate and Restart
```
