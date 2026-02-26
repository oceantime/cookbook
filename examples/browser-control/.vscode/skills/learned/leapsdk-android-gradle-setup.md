# LeapSDK Android Gradle 项目集成配置

> **适用范围**: 本项目（BrowserControlDemo）  
> **标签**: leapsdk, android, gradle, kotlin-dsl, github-packages, arm64, proguard

---

## 1. settings.gradle.kts：GitHub Packages 认证

LeapSDK 发布在 GitHub Packages 私有仓库，需要配置 Maven 仓库 + 凭证：

```kotlin
// settings.gradle.kts
dependencyResolutionManagement {
    repositories {
        google()
        mavenCentral()
        maven {
            url = uri("https://maven.pkg.github.com/liquid4all/LeapSDK-Android")
            credentials {
                // 优先读环境变量，本地开发用 gradle.properties
                username = providers.gradleProperty("gpr.user").orNull
                    ?: System.getenv("GITHUB_USERNAME") ?: ""
                password = providers.gradleProperty("gpr.token").orNull
                    ?: System.getenv("GITHUB_TOKEN") ?: ""
            }
        }
    }
}
```

**⚠️ 注意**：`settings.gradle.kts` 中不能用 `project.findProperty()`（settings 阶段无 project 对象），必须用 `providers.gradleProperty("key").orNull`。

**本地开发**（`~/.gradle/gradle.properties`）：
```properties
gpr.user=your_github_username
gpr.token=ghp_xxxxxxxxxxxxxxxxxxxx
```

---

## 2. app/build.gradle.kts：核心配置

```kotlin
android {
    compileSdk = 34
    defaultConfig {
        minSdk = 31
        targetSdk = 34
        ndk {
            abiFilters += listOf("arm64-v8a")   // 仅 ARM64，移除 x86 减小 APK
        }
    }
    buildFeatures { compose = true }
    composeOptions { kotlinCompilerExtensionVersion = "1.5.3" }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    // LeapSDK
    implementation("ai.liquid.leap:leap-sdk:0.9.7")
    implementation("ai.liquid.leap:leap-model-downloader:0.9.7")

    // Compose
    implementation(platform("androidx.compose:compose-bom:2023.10.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.activity:activity-compose:1.8.2")

    // WebView
    implementation("androidx.webkit:webkit:1.9.0")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
}
```

---

## 3. AndroidManifest.xml：必要权限

```xml
<!-- 模型下载 + WebView 加载本地 HTTP 服务 -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<!-- 模型文件读写（Android <= 12） -->
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"
    android:maxSdkVersion="32" />
<!-- Android 13+ 读 /sdcard 需要 MANAGE_EXTERNAL_STORAGE，运行时申请 -->

<application
    android:usesCleartextTraffic="true"   <!-- 允许 HTTP（本地 Docker 服务）-->
    ...>
```

---

## 4. ProGuard 规则

```pro
# app/proguard-rules.pro
-keep class ai.liquid.leap.** { *; }
-keepclassmembers class ai.liquid.leap.** { *; }
```

---

## 5. 版本组合（已验证）

| 组件 | 版本 |
|------|------|
| AGP | 8.2.2 |
| Kotlin | 1.9.10 |
| Gradle | 8.2 |
| Compose BOM | 2023.10.01 |
| Compose Compiler | 1.5.3 |
| LeapSDK | 0.9.7 |
| minSdk | 31 |
| compileSdk | 34 |

---

## 6. arm64-v8a only 的原因

- GGML 推理依赖 ARM NEON/SVE 指令集，x86_64 模拟器运行会 `SIGILL` 崩溃
- 移除 x86 ABI 可减小 APK 体积约 40%
- 所有现代 Android 手机均为 ARM64

---

## 7. 编译机 vs 测试设备

| 角色 | 架构要求 | 原因 |
|------|---------|------|
| 编译机（`./gradlew assembleDebug`）| **x86_64** | `aapt2`/`d8` 只有 x86_64 Linux 版本 |
| 测试设备（运行推理）| **ARM64** | GGML 需要 ARM NEON |

ARM64 编译机跑 `./gradlew assembleDebug` 会报：`cannot execute binary file: Exec format error`
