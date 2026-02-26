# Skill: Android App 图标资源完整结构

**类别**: Android 开发  
**适用场景**: 新建 Android 项目缺少图标资源，构建报 AAPT 错误  
**创建时间**: 2026-02-22

---

## 问题现象

```
AAPT: error: resource mipmap/ic_launcher (aka ai.liquid.xxx:mipmap/ic_launcher) not found.
```

---

## 原因

AndroidManifest.xml 引用了 `@mipmap/ic_launcher` 和 `@mipmap/ic_launcher_round`，
但项目中缺少对应的 mipmap 资源文件。

---

## 完整的图标资源文件结构

```
res/
├── drawable/
│   ├── ic_launcher_background.xml   # 图标背景（矢量）
│   └── ic_launcher_foreground.xml   # 图标前景（矢量）
├── mipmap-anydpi-v26/               # Android 8.0+ 自适应图标
│   ├── ic_launcher.xml
│   └── ic_launcher_round.xml
├── mipmap-mdpi/                     # 中密度屏幕
│   ├── ic_launcher.xml
│   └── ic_launcher_round.xml
├── mipmap-hdpi/                     # 高密度屏幕
│   ├── ic_launcher.xml
│   └── ic_launcher_round.xml
├── mipmap-xhdpi/                    # 超高密度屏幕
│   ├── ic_launcher.xml
│   └── ic_launcher_round.xml
├── mipmap-xxhdpi/                   # 超超高密度屏幕
│   ├── ic_launcher.xml
│   └── ic_launcher_round.xml
└── mipmap-xxxhdpi/                  # 最高密度屏幕
    ├── ic_launcher.xml
    └── ic_launcher_round.xml
```

---

## 各文件内容模板

### drawable/ic_launcher_background.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#3DDC84"
        android:pathData="M0,0h108v108h-108z" />
</vector>
```

### drawable/ic_launcher_foreground.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <!-- 自定义前景图案 -->
</vector>
```

### mipmap-anydpi-v26/ic_launcher.xml（自适应图标）
```xml
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
```

### mipmap-{density}/ic_launcher.xml（各密度兼容图标）
```xml
<?xml version="1.0" encoding="utf-8"?>
<bitmap xmlns:android="http://schemas.android.com/apk/res/android"
    android:src="@drawable/ic_launcher_foreground" />
```

---

## 快速解决方法

使用 Android Studio 的 **Image Asset Studio** 自动生成所有密度的图标：

1. 右键点击 `res` 目录
2. 选择 **New → Image Asset**
3. 选择图标类型（Launcher Icons）
4. 配置前景/背景
5. 点击 **Finish** 自动生成所有密度文件

---

## 注意事项

- `mipmap-anydpi-v26` 用于 Android 8.0+（API 26+），支持自适应图标
- 各密度目录用于 Android 8.0 以下的兼容性
- `minSdk=31` 时理论上只需要 `anydpi-v26`，但保留其他密度更安全
- PNG 格式的图标需要分别提供各密度的不同尺寸文件（48/72/96/144/192 dp）
