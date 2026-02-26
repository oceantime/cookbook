# browser-control 项目技能手册

> **目的**: browser-control 项目的技术技能索引和提取规则  
> **受众**: 在此项目上工作的开发者和 AI 代理  
> **最后更新**: 2026-02-26（新增 DGX SPARK B10 + Docker 本地训练环境技能，归纳 STAGE1/STAGE2 验证结果）

---

## 📌 技能提取规则

每次会话结束时，按以下步骤提取技能：

1. 回顾当前会话，寻找可提取的经验
2. 识别最有价值的洞察
3. 确定保存位置（全局 vs 项目）
4. 起草 skill 文件
5. 进行质量自评
6. 展示给用户确认
7. 保存 skill 文件到指定路径
8. 更新本文件的技能索引表

## 📂 技能保存路径

- **全局**（跨项目通用）: `C:\Users\27575\.vscode\skills\learned\`
- **项目内**（本项目专属）: `.vscode/skills/learned/`

---

## 📋 技能索引

使用 `/skills <命令>` 快速查找技能文件：

| 技能名称 | 命令 | 使用说明 | 文件目录 |
|---------|------|---------|---------|
| GRPO 强化学习 | `/skills grpo` | 组相对策略优化原理，TRL 实现，调试配置，训练基准 | `.vscode/skills/learned/grpo-reinforcement-learning.md` |
| 模型量化 GGUF | `/skills gguf` | 量化方法对比（FP16/Q8/Q5/Q4），转换管道，推理基准（run31 Q8_0: 116.2 t/s prompt / 15.2 t/s gen） | `.vscode/skills/learned/model-quantization-gguf.md` |
| ARM64 + CUDA 13 开发 | `/skills arm64` | ARM64 平台 PyTorch 配置，DGX Spark，CUDA 版本支持矩阵 | `.vscode/skills/learned/arm64-cuda-development.md` |
| Modal 无服务器 GPU | `/skills modal` | 镜像/函数/存储卷/密钥，Volume commit，远程开发模式 | `.vscode/skills/learned/modal-serverless-gpu.md` |
| BrowserGym 环境 | `/skills browsergym` | 观察类型（DOM/AXTree），HTTP REST 接口，action 格式（bid 字符串），观察字段表，last_action_error | `.vscode/skills/learned/browsergym-environment.md` |
| uv 包管理器 | `/skills uv` | 常用命令，自定义包索引（PyTorch ARM64），锁文件 | `.vscode/skills/learned/uv-package-manager.md` |
| 模型检查点管理 | `/skills checkpoint` | 命名约定，Modal Volume 存储，WandB 监控，备份策略，**Docker Volume 检查点提取（alpine cp 方案）** | `.vscode/skills/learned/checkpoint-management.md` |
| 常见错误处理模式 | `/skills errors` | subprocess Unicode，Modal Volume 并发，BrowserGym 休眠，Kotlin FIR 崩溃 | `.vscode/skills/learned/error-handling-patterns.md` |
| Android 构建版本兼容性链 | `/skills android-build` | AGP/Kotlin/Gradle/Java/SDK 版本对应关系，升级步骤，清理缓存 | `.vscode/skills/learned/android-build-compatibility.md` |
| Kotlin K2 FIR 崩溃修复 | `/skills kotlin-k2-fix` | K2 编译器 FirIncompatibleClassExpressionChecker 崩溃，`-Xskip-metadata-version-check` 参数 | `.vscode/skills/learned/kotlin-k2-fir-incompatible-class-fix.md` |
| Android App 图标资源结构 | `/skills android-icon` | mipmap 资源完整目录结构，自适应图标，各密度文件模板 | `.vscode/skills/learned/android-mipmap-icon-setup.md` |
| Android SELinux adb 权限 | `/skills android-selinux` | adb push 文件 app 无法访问，run-as cp 解决方案，listFiles() vs exists() | `.vscode/skills/learned/android-selinux-adb-file-permissions.md` |
| Android LLM 推理线程模型 | `/skills android-threading` | Dispatchers.Default/IO/Main 分工，WebView 必须主线程，flowOn 用法 | `.vscode/skills/learned/android-llm-inference-threading.md` |
| LeapSDK 本地模型加载 | `/skills leapsdk-local` | GGUF+JSON 双文件要求，离线构建命令，API 参数名，路径对照表 | `.vscode/skills/learned/leapsdk-local-model-loading.md` |
| LeapSDK Android Gradle 集成 | `/skills leapsdk-gradle` | GitHub Packages Maven 认证，arm64 ABI，ProGuard，Manifest 权限，编译机/测试设备分工 | `.vscode/skills/learned/leapsdk-android-gradle-setup.md` |
| MiniWoB JS API 交互 | `/skills miniwob-js` | endEpisode 拦截持久化 reward、timer 延长、viewport 幂等注入 | `.vscode/skills/learned/miniwob-js-api-interaction.md` |
| safetensors→GGUF 转换 | `/skills gguf-pipeline` | HF 下载→F16→Q8_0 三步流水线，量化级别对比，JSON manifest 复用规则 | `~/.vscode/skills/learned/safetensors-to-gguf-pipeline.md` |
| Android WebView JS Bridge | `/skills webview-bridge` | suspendCancellableCoroutine 包装 evaluateJavascript，线程分工，结果类型处理 | `~/.vscode/skills/learned/android-webview-kotlin-js-bridge.md` |
| LeapSDK 模型替换 | `/skills leapsdk-swap` | 只换 .gguf 不换 .json，两个可用模型路径，验证步骤 | `.vscode/skills/learned/leapsdk-model-swap.md` |
| Docker Playwright Debian Trixie | `/skills playwright-debian` | Debian Trixie 字体包命名，手动预安装依赖，playwright install 参数 | `.vscode/skills/learned/docker-playwright-debian-trixie.md` |
| TRL rollout_func + vLLM Server | `/skills trl-rollout` | rollout_func 签名（版本相关），colocate vs server 模式，extra_fields→reward_func 接线，VLLMClient 接口 | `.vscode/skills/learned/trl-rollout-func-vllm-server.md` |
| GRPO reward_func 接线 | `/skills grpo-reward` | rollout_func extra_fields 透传机制，reward_func 从 kwargs 读取 reward，reward_funcs=[] 陷阱，run20→run23 对比验证 | `.vscode/skills/learned/grpo-reward-func-from-rollout.md` |
| GRPO entropy 崩溃与 reward_std=0 死锁 | `/skills grpo-entropy` | 崩溃时间线，reward_std=0→advantage=0→无梯度，LR=1e-6 修复，任务多样性治本，诊断清单 | `.vscode/skills/learned/grpo-entropy-collapse-reward-std-zero.md` |
| DGX SPARK B10 + Docker 本地训练环境 | `/skills dgx-docker` | GB10 硬件配置验证，Docker Compose 服务架构（training/browsergym/tensorboard），训练容器依赖栈，GB10 必须用 vllm_mode=colocate，Makefile 目标速查 | `.vscode/skills/learned/dgx-docker-local-training-setup.md` |
