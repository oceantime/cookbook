# Docker Playwright Debian Trixie 构建技能

> **创建时间**: 2026-02-24  
> **适用场景**: 在 Debian Trixie 基础镜像上构建 Playwright + Chromium 的 Docker 容器  
> **关键技术**: Docker, Playwright, Debian 包管理, BrowserGym

---

## 🎯 问题描述

在使用 `python:3.11-slim` (Debian Trixie) 作为基础镜像构建包含 Playwright 的 Docker 容器时，遇到系统依赖安装失败：

```bash
E: Package 'ttf-unifont' has no installation candidate
E: Package 'ttf-ubuntu-font-family' has no installation candidate
```

**错误位置**：`playwright install chromium --with-deps` 尝试安装系统依赖时

**根本原因**：
1. Debian Trixie 中字体包已重命名：`ttf-unifont` → `fonts-unifont`
2. Playwright 1.49.1 的依赖列表针对 Ubuntu 20.04，在 Debian Trixie 上包名不兼容
3. Playwright 提示："BEWARE: your OS is not officially supported by Playwright"

---

## ✅ 解决方案

### 方法：手动预安装系统依赖 + 仅下载浏览器

**Dockerfile 最佳实践**：

```dockerfile
FROM python:3.11-slim

# 1. 手动安装 Debian Trixie 兼容的字体和依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    chromium \
    chromium-driver \
    xvfb \
    x11vnc \
    fluxbox \
    fonts-unifont \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. 安装 Playwright，但只下载浏览器（不安装系统依赖）
RUN pip install --no-cache-dir --default-timeout=300 playwright==1.49.1 && \
    python -m playwright install chromium
    # 注意：不使用 --with-deps，因为系统依赖已经手动安装
```

### 关键点说明

| 配置项 | 错误方式 | 正确方式 | 原因 |
|--------|---------|---------|------|
| 字体包 | `ttf-unifont` | `fonts-unifont` | Debian Trixie 新命名规则 |
| Ubuntu 字体 | `fonts-ubuntu` | 移除（或使用 `fonts-ubuntu-title`） | Trixie 中不存在此包 |
| Playwright 安装 | `playwright install chromium --with-deps` | `playwright install chromium` | 手动控制依赖安装 |
| 跳过依赖参数 | ❌ `--skip-install-deps` | ✅ 不使用参数 | 该参数不存在 |

---

## 🔍 诊断步骤

### 1. 检查包名是否可用

```bash
# 在 Debian Trixie 容器内测试
docker run --rm python:3.11-slim bash -c "
  apt-get update > /dev/null 2>&1 && \
  apt-cache show fonts-unifont | head -5
"
```

**预期输出**：显示包信息（说明包存在）

### 2. 查看 Playwright 支持的选项

```bash
docker run --rm python:3.11-slim bash -c "
  pip install playwright > /dev/null 2>&1 && \
  python -m playwright install --help
"
```

**关键选项**：
- `--with-deps`：安装系统依赖（会失败）
- 默认（无参数）：仅下载浏览器二进制（推荐）

### 3. 验证字体包已安装

```bash
docker run --rm your-image:latest dpkg -l | grep fonts-
```

---

## 📊 依赖版本参考

### 成功构建的包版本

| 组件 | 版本 | 来源 |
|------|------|------|
| 基础镜像 | `python:3.11-slim` | Debian Trixie |
| Playwright | 1.49.1 → 1.44.0 | pip（自动降级） |
| Chromium | Debian 包 + Playwright 二进制 | 双重安装 |
| 字体包 | `fonts-unifont 1:15.1.01-1` | Debian Trixie |

**注意**：Playwright 会被 `browsergym-core==0.14.2` 降级到 1.44.0（依赖要求）

---

## 🚨 常见陷阱

### ❌ 错误 1：使用不存在的参数

```dockerfile
# 错误
RUN python -m playwright install chromium --skip-install-deps
# 报错：error: unknown option '--skip-install-deps'
```

**修正**：移除参数，仅使用 `install chromium`

### ❌ 错误 2：信任 Playwright 自动检测

```dockerfile
# 有风险
RUN python -m playwright install chromium --with-deps
# Playwright 会尝试安装 Ubuntu 20.04 的包名，在 Trixie 上失败
```

**修正**：手动预安装依赖，让 Playwright 仅下载浏览器

### ❌ 错误 3：字体包使用旧命名

```dockerfile
# 错误
RUN apt-get install -y ttf-unifont fonts-ubuntu
# 报错：Package 'ttf-unifont' has no installation candidate
```

**修正**：使用新命名 `fonts-unifont`，移除不存在的包

---

## 🎓 延伸知识

### Debian 字体包命名变更历史

| Debian 版本 | 旧命名 | 新命名 | 变更时间 |
|------------|--------|--------|---------|
| Jessie (8) | `ttf-*` | - | 2015 |
| Stretch (9) | 混合 | `fonts-*` | 2017 |
| Trixie (13) | - | `fonts-*` | 2024+ |

### Playwright 官方支持的操作系统

- ✅ Ubuntu 20.04, 22.04, 24.04
- ✅ Debian 11 (Bullseye), 12 (Bookworm)
- ⚠️ Debian Trixie (测试版) - 不官方支持

---

## 📚 相关资源

- [Playwright 系统要求](https://playwright.dev/docs/intro#system-requirements)
- [Debian 字体包列表](https://packages.debian.org/trixie/fonts/)
- [Debian Trixie 发行说明](https://www.debian.org/releases/trixie/)

---

## ✅ 验证清单

构建成功后，确认以下内容：

- [ ] 镜像大小合理（5-6GB）
- [ ] 字体包已安装：`dpkg -l | grep fonts-unifont`
- [ ] Chromium 可执行：`chromium --version`
- [ ] Playwright 浏览器已下载：`playwright-core`
- [ ] 容器启动无错误：`docker compose up browsergym`

---

**标签**: `#docker` `#playwright` `#debian-trixie` `#browsergym` `#troubleshooting`
