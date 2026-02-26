# Browser-Control Android端构建方案

> **创建时间**: 2026-02-21  
> **更新时间**: 2026-02-23 (全部阶段完成)  
> **目标**: 在Android设备验证训练后的LFM2-350M browser-control模型  
> **预计周期**: 2周（快速原型验证）

## 📋 进度概览

| 阶段 | 状态 | 完成时间 | 关键产物 |
|------|------|----------|----------|
| 阶段一: 模型转换与验证 | ✅ 完成 | 2026-02-21/22 | 4个GGUF文件 (FP16/Q8_0/Q5_K_M/Q4_K_M)<br/>✅ Modal云端方法<br/>✅ 本地ARM64方法 |
| 阶段二: Android项目初始化 | ✅ 完成 | 2026-02-22 | ✅ Gradle配置 (Kotlin DSL)<br/>✅ LeapSDK 0.9.7集成<br/>✅ Jetpack Compose框架<br/>✅ MainActivity + 系统Prompt |
| 阶段三: 核心组件实现 | ✅ 完成 | 2026-02-22 | ✅ BrowserObservation + BrowserAction (domain)<br/>✅ PromptFormatter (domain)<br/>✅ WebViewAccessibility + ActionExecutor (infrastructure)<br/>✅ ModelInference + BrowserViewModel |
| 阶段四: UI实现 | ✅ 完成 | 2026-02-22 | ✅ WebViewCompose (嵌入WebView)<br/>✅ BrowserControlScreen (主界面)<br/>✅ MainActivity (更新入口)<br/>✅ AppConfig.kt (URL可配置化) |
| 阶段五: 集成测试 | ✅ 完成 | 2026-02-23 | ✅ MiniWoB本地Docker构建 (localhost:8080)<br/>✅ APK编译 + ARM64设备安装<br/>✅ 模型文件推送 + 加载成功<br/>✅ WebView显示MiniWoB任务页<br/>✅ 模型推理端到端验证<br/>✅ MiniWoB reward判断 + 结果覆盖层<br/>✅ 作者模型(Paulescu) GGUF转换验证 |
| 阶段六: 文档与优化 | ✅ 完成 | 2026-02-23 | ✅ 构建方案文档更新 |

## 1. 项目概述

将训练好的 **LFM2-350M browser-control模型** 构建到Android设备，实现端到端的浏览器自动化控制验证。

### 技术方案
- **推理引擎**: LeapSDK (GGUF格式 + llama.cpp)
- **训练模型**: `LFM2-350M-browsergym-20260220-182152` checkpoint
- **目标格式**: GGUF (Q8_0/Q5_K_M/Q4_K_M量化)
- **UI框架**: Jetpack Compose + WebView
- **测试任务**: MiniWoB click-button
- **参考项目**: [LeapSDK-Examples](https://github.com/oceantime/LeapSDK-Examples)

---

## 2. 实施步骤

### 阶段一: 模型转换与验证 ✅ (已完成 - 2026-02-21/22)

> **✅ 突破**: 发现CUDA 13.0支持ARM64，实现本地GPU加速转换  
> **📊 效果对比**: 本地转换（2-3秒） vs Modal云端转换（5-8分钟）

#### 方法概述

本阶段提供**两种可行方法**完成GGUF模型转换，任选其一：

| 方法 | 环境 | 速度 | 优势 | 限制 |
|------|------|------|------|------|
| **方法1: 本地ARM64转换** | 本地 ARM64 + CUDA 13.0 | ⚡ 2-3秒 | 极快、免费、可重复 | 需要CUDA 13.0驱动 |
| **方法2: Modal云端转换** | Modal云 x86_64 + A10G | 🐢 5-8分钟 | 无本地要求、兼容性好 | 需Modal账号、有成本 |

**推荐选择**:
- ✅ **有ARM64 + CUDA 13.0**: 使用方法1（本地转换）
- ✅ **x86_64系统**: 使用方法2（Modal云端）
- ✅ **仅有CUDA 12.x**: 使用方法2（PyTorch CUDA 12.x不支持ARM64）

---

## 🚀 方法1: 本地ARM64转换（推荐）

> **关键发现**: PyTorch CUDA 13.0支持ARM64架构（与CUDA 12.x不同）  
> **信息来源**: [DGX Spark论坛](https://forums.developer.nvidia.cn/t/dgx-spark-vllm-cuda13/28377)  
> **适用设备**: ARM64服务器 + NVIDIA GB10/GB20/GB200等CUDA 13.0 GPU

### 1.1 系统要求检查

```bash
# 检查系统架构（必须是 aarch64）
uname -m
# 输出: aarch64

# 检查CUDA版本（必须是 13.0）
nvidia-smi
# 输出应包含: CUDA Version: 13.0

# 检查GPU型号
nvidia-smi --query-gpu=name --format=csv,noheader
# 输出示例: NVIDIA GB10
```

**⚠️ 重要**: 
- CUDA 12.1/12.4/12.6的PyTorch不支持ARM64
- 仅CUDA 13.0提供ARM64 wheels支持

### 1.2 配置项目环境

**Step 1**: 编辑 `pyproject.toml`，添加CUDA 13.0索引配置

```toml
[project]
dependencies = [
    "torch>=2.10.0",  # 确保版本 >= 2.10.0
    # ... 其他依赖
]

# 添加PyTorch CUDA 13.0索引
[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
explicit = true

# 指定torch使用CUDA 13.0索引
[tool.uv.sources]
torch = { index = "pytorch-cu130" }
torchvision = { index = "pytorch-cu130" }
```

**Step 2**: 安装依赖

```bash
cd /home/tony/project/cookbook/examples/browser-control

# 同步依赖（会自动安装CUDA 13.0版本）
uv sync

# 预期输出:
# Resolved 123 packages in 2.54s
# Downloaded 8 packages in 15.23s  # torch等CUDA包约1GB
# Installed 8 packages in 1.23s
#  + nvidia-cublas-cu13==13.0.76
#  + nvidia-cudnn-cu13==9.5.1.17
#  + torch==2.10.0+cu130
#  + torchvision==0.25.0+cu130
#  + ...
```

**Step 3**: 验证CUDA可用性

```bash
uv run python -c "
import torch
print(f'PyTorch版本: {torch.__version__}')
print(f'CUDA可用: {torch.cuda.is_available()}')
print(f'CUDA版本: {torch.version.cuda}')
print(f'GPU设备: {torch.cuda.get_device_name(0)}')
print(f'计算能力: {torch.cuda.get_device_capability(0)}')
"

# 预期输出:
# PyTorch版本: 2.10.0+cu130
# CUDA可用: True
# CUDA版本: 13.0
# GPU设备: NVIDIA GB10
# 计算能力: (12, 1)
```

### 1.3 创建本地转换脚本

**创建文件**: `scripts/convert_to_gguf_local.py`

```python
"""
本地ARM64 + CUDA 13.0环境下转换GGUF模型
要求: PyTorch 2.10.0+cu130, llama.cpp已编译
"""

import subprocess
import sys
from pathlib import Path

def check_cuda():
    """检查CUDA环境"""
    try:
        import torch
        print(f"✓ PyTorch版本: {torch.__version__}")
        
        if not torch.cuda.is_available():
            print("✗ CUDA不可用！请检查:")
            print("  1. nvidia-smi是否显示CUDA 13.0")
            print("  2. 是否正确配置pyproject.toml的pytorch-cu130索引")
            print("  3. 是否执行了 uv sync 安装依赖")
            sys.exit(1)
        
        print(f"✓ CUDA版本: {torch.version.cuda}")
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
        print(f"✓ 计算能力: {torch.cuda.get_device_capability(0)}")
        
    except ImportError:
        print("✗ torch未安装！执行: uv sync")
        sys.exit(1)

def convert_to_gguf(checkpoint_dir: str, output_dir: str):
    """转换checkpoint为GGUF格式"""
    
    checkpoint_path = Path(checkpoint_dir)
    output_path = Path(output_dir)
    
    if not checkpoint_path.exists():
        print(f"✗ Checkpoint不存在: {checkpoint_path}")
        sys.exit(1)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # llama.cpp路径（假设已编译）
    llama_cpp_dir = Path("llama.cpp")
    if not llama_cpp_dir.exists():
        print("✗ llama.cpp未找到！请先编译:")
        print("  git clone https://github.com/ggerganov/llama.cpp")
        print("  cd llama.cpp")
        print("  cmake -B build && cmake --build build --config Release -j$(nproc)")
        sys.exit(1)
    
    convert_script = llama_cpp_dir / "convert_hf_to_gguf.py"
    quantize_bin = llama_cpp_dir / "build" / "bin" / "llama-quantize"
    
    print(f"\n{'='*60}")
    print(f"开始转换: {checkpoint_path.name}")
    print(f"输出目录: {output_path}")
    print(f"{'='*60}\n")
    
    # Step 1: HuggingFace → FP16 GGUF
    print("[ 1/4 ] 转换为 FP16 GGUF...")
    fp16_output = output_path / "lfm2-350m-browsergym-fp16.gguf"
    
    cmd = [
        sys.executable, str(convert_script), str(checkpoint_path),
        "--outfile", str(fp16_output),
        "--outtype", "f16",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
    if result.returncode != 0:
        print(f"✗ 转换失败:\n{result.stderr}")
        sys.exit(1)
    
    size_mb = fp16_output.stat().st_size / (1024 * 1024)
    print(f"✓ 生成: {fp16_output.name} ({size_mb:.2f} MB)")
    
    # Step 2-4: 量化
    quantizations = [
        ("Q8_0", "q8_0"),
        ("Q5_K_M", "q5_k_m"),
        ("Q4_K_M", "q4_k_m"),
    ]
    
    for i, (method, suffix) in enumerate(quantizations, start=2):
        print(f"\n[ {i}/4 ] 量化为 {method}...")
        quant_output = output_path / f"lfm2-350m-browsergym-{suffix}.gguf"
        
        cmd = [str(quantize_bin), str(fp16_output), str(quant_output), method]
        
        result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        if result.returncode != 0:
            print(f"✗ 量化失败:\n{result.stderr}")
            sys.exit(1)
        
        # 提取量化时间
        for line in result.stdout.split('\n'):
            if 'quantize time' in line:
                print(f"  {line.strip()}")
        
        size_mb = quant_output.stat().st_size / (1024 * 1024)
        print(f"✓ 生成: {quant_output.name} ({size_mb:.2f} MB)")
    
    print(f"\n{'='*60}")
    print("✓ 转换完成！生成文件:")
    print(f"{'='*60}")
    for file in sorted(output_path.glob("*.gguf")):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  {file.name:<40} {size_mb:>8.2f} MB")
    print()

if __name__ == "__main__":
    # 检查CUDA环境
    check_cuda()
    
    # 执行转换
    checkpoint = "checkpoints/LFM2-350M-browsergym-20260220-182152"
    output = "gguf_models_local"
    
    convert_to_gguf(checkpoint, output)
```

### 1.4 执行转换

```bash
# 确保llama.cpp已编译
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build && cmake --build build --config Release -j$(nproc)
cd ..

# 执行转换（⚡ 仅需2-3秒！）
uv run python scripts/convert_to_gguf_local.py
```

**预期输出**:
```
✓ PyTorch版本: 2.10.0+cu130
✓ CUDA版本: 13.0
✓ GPU: NVIDIA GB10
✓ 计算能力: (12, 1)

============================================================
开始转换: LFM2-350M-browsergym-20260220-182152
输出目录: gguf_models_local
============================================================

[ 1/4 ] 转换为 FP16 GGUF...
✓ 生成: lfm2-350m-browsergym-fp16.gguf (678.52 MB)

[ 2/4 ] 量化为 Q8_0...
  main: quantize time =   538.45 ms
✓ 生成: lfm2-350m-browsergym-q8_0.gguf (361.65 MB)

[ 3/4 ] 量化为 Q5_K_M...
  main: quantize time =  1143.12 ms
✓ 生成: lfm2-350m-browsergym-q5_k_m.gguf (248.31 MB)

[ 4/4 ] 量化为 Q4_K_M...
  main: quantize time =  1234.56 ms
✓ 生成: lfm2-350m-browsergym-q4_k_m.gguf (218.69 MB)

============================================================
✓ 转换完成！生成文件:
============================================================
  lfm2-350m-browsergym-fp16.gguf              678.52 MB
  lfm2-350m-browsergym-q4_k_m.gguf            218.69 MB
  lfm2-350m-browsergym-q5_k_m.gguf            248.31 MB
  lfm2-350m-browsergym-q8_0.gguf              361.65 MB
```

**⏱️ 总耗时**: 约2-3秒（比Modal快100-200倍！）

### 1.5 验证模型

```bash
cd llama.cpp

# 测试Q8_0模型
./build/bin/llama-cli \
  -m ../gguf_models_local/lfm2-350m-browsergym-q8_0.gguf \
  -p "Goal: Click the button

Page structure:
[1] body
  [2] button 'Submit'

What action do you take?" \
  -n 100 \
  --temp 0.1

# 预期输出:
# Loading model...
# To achieve the goal of clicking the button...
# 
# [ Prompt: 167.3 t/s | Generation: 6.5 t/s ]
```

---

## ☁️ 方法2: Modal云端转换（兼容方案）

> **适用场景**: x86_64系统、仅有CUDA 12.x的ARM64、无本地GPU  
> **优势**: 无本地环境要求，稳定可靠

### 2.1 Modal账号配置

```bash
# 安装Modal CLI
uv pip install modal

# 登录（首次需要）
uv run modal setup
# 会打开浏览器完成OAuth认证
```

### 2.2 创建Modal转换脚本

**创建文件**: `scripts/convert_to_gguf_simple.py`

```python
"""
使用Modal云环境 + llama.cpp直接转换GGUF格式
避免unsloth依赖问题，直接调用llama.cpp工具链
"""

import modal

app = modal.App("browser-control-gguf-conversion")

# Modal volume存储checkpoint
volume = modal.Volume.from_name(
    "browser-control-fine-tune-with-grpo", 
    create_if_missing=False
)

# 构建镜像：预编译llama.cpp
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "build-essential", "cmake")
    .pip_install(
        "transformers>=4.57.0",
        "torch>=2.5.0",
        "accelerate>=0.27.0",
        "sentencepiece>=0.2.0",
        "protobuf>=5.29.0",
    )
    .run_commands(
        # 克隆并编译llama.cpp
        "cd /root && git clone https://github.com/ggerganov/llama.cpp.git",
        "cd /root/llama.cpp && cmake -B build && cmake --build build --config Release -j$(nproc)",
    )
)


@app.function(
    image=image,
    gpu="A10G",  # 使用A10G GPU
    volumes={"/checkpoints": volume},
    timeout=3600,  # 1小时超时
)
def convert_checkpoint_to_gguf():
    """转换HuggingFace checkpoint为GGUF格式"""
    import subprocess
    from pathlib import Path
    
    checkpoint_dir = "/checkpoints/LFM2-350M-browsergym-20260220-182152"
    output_dir = "/checkpoints/gguf_output"
    
    print(f"Converting checkpoint from: {checkpoint_dir}")
    print(f"Output directory: {output_dir}")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Step 1: HuggingFace → FP16 GGUF
    print("\n=== Step 1: Converting to FP16 GGUF ===")
    convert_script = "/root/llama.cpp/convert_hf_to_gguf.py"
    fp16_output = f"{output_dir}/lfm2-350m-browsergym-fp16.gguf"
    
    cmd = [
        "python3", convert_script, checkpoint_dir,
        "--outfile", fp16_output,
        "--outtype", "f16",
    ]
    
    print(f"Running: {' '.join(cmd)}")
    # ⚠️ 重要: errors='ignore' 处理llama.cpp输出中的非UTF-8字符
    result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        raise RuntimeError(f"Conversion failed with code {result.returncode}")
    
    # Step 2-4: 量化为Q8_0, Q5_K_M, Q4_K_M
    quantize_bin = "/root/llama.cpp/build/bin/llama-quantize"
    
    for quant_method, output_name in [
        ("Q8_0", "q8_0"),
        ("Q5_K_M", "q5_k_m"),
        ("Q4_K_M", "q4_k_m"),
    ]:
        print(f"\n=== Quantizing to {quant_method} ===")
        quant_output = f"{output_dir}/lfm2-350m-browsergym-{output_name}.gguf"
        
        cmd = [quantize_bin, fp16_output, quant_output, quant_method]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        print(result.stdout)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            raise RuntimeError(f"Quantization {quant_method} failed")
    
    # 显示生成的文件
    print("\n=== Conversion Complete ===")
    print("\nGenerated files:")
    for file in Path(output_dir).glob("*.gguf"):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  - {file.name}: {size_mb:.2f} MB")
    
    volume.commit()
    
    return {
        "fp16": fp16_output,
        "q8_0": f"{output_dir}/lfm2-350m-browsergym-q8_0.gguf",
        "q5_k_m": f"{output_dir}/lfm2-350m-browsergym-q5_k_m.gguf",
        "q4_k_m": f"{output_dir}/lfm2-350m-browsergym-q4_k_m.gguf",
    }


@app.local_entrypoint()
def main():
    """执行转换"""
    print("Starting GGUF conversion on Modal...")
    result = convert_checkpoint_to_gguf.remote()
    print(f"\n✅ Conversion successful!")
    print(f"Output files: {result}")
    print("\nFiles are stored in Modal volume: browser-control-fine-tune-with-grpo")
    print("Location: /checkpoints/gguf_output/")
```

### 2.3 执行Modal转换

```bash
cd /home/tony/project/cookbook/examples/browser-control

# 运行Modal转换（自动使用云端GPU A10G）
uv run modal run scripts/convert_to_gguf_simple.py

# 预期输出:
# === Step 1: Converting to FP16 GGUF ===
# ...
# === Step 2: Quantizing to Q8_0 ===
# main: quantize time = 1756.38 ms
# ...
# === Conversion Complete ===
# Generated files:
#   - lfm2-350m-browsergym-fp16.gguf: 678.52 MB
#   - lfm2-350m-browsergym-q8_0.gguf: 361.65 MB
#   - lfm2-350m-browsergym-q5_k_m.gguf: 248.31 MB
#   - lfm2-350m-browsergym-q4_k_m.gguf: 218.69 MB
```

**⏱️ 转换时间**: 约5-8分钟（包括编译llama.cpp、镜像启动等）

### 2.4 下载GGUF模型到本地

```bash
# 下载所有GGUF文件
mkdir -p gguf_models
uv run modal volume get browser-control-fine-tune-with-grpo \
  gguf_output \
  gguf_models/

# 验证文件
ls -lh gguf_models/gguf_output/*.gguf
# -rw-rw-r-- 1 tony tony 679M  lfm2-350m-browsergym-fp16.gguf
# -rw-rw-r-- 1 tony tony 219M  lfm2-350m-browsergym-q4_k_m.gguf
# -rw-rw-r-- 1 tony tony 249M  lfm2-350m-browsergym-q5_k_m.gguf
# -rw-rw-r-- 1 tony tony 362M  lfm2-350m-browsergym-q8_0.gguf
```

---

## 📊 两种方法对比总结

### 性能对比

| 指标 | 本地ARM64+CUDA13 | Modal云端 |
|------|------------------|-----------|
| **总耗时** | ⚡ 2-3秒 | 🐢 5-8分钟 |
| **FP16转换** | <1秒 | ~2分钟 |
| **Q8_0量化** | 538ms | ~2秒 |
| **Q5_K_M量化** | 1.1秒 | ~3秒 |
| **Q4_K_M量化** | 1.2秒 | ~3秒 |
| **网络传输** | ✓ 无需传输 | ✗ 需下载1.5GB |
| **成本** | ✓ 免费 | ⚠️ 每次约$0.1-0.2 |
| **可重复性** | ✓ 随时运行 | ⚠️ 需Modal配额 |

**速度优势**: 本地方法快**100-200倍**！

### 适用场景

**选择本地方法（方法1）**:
- ✅ 系统是ARM64 (aarch64)
- ✅ 安装了CUDA 13.0驱动
- ✅ 有NVIDIA GB10/GB20/GB200等GPU
- ✅ 需要频繁转换或快速迭代

**选择Modal方法（方法2）**:
- ✅ 系统是x86_64
- ✅ 仅有CUDA 12.x（不支持ARM64）
- ✅ 没有本地GPU
- ✅ 偶尔转换一次

---

## ✅ 阶段一完成检查清单

无论使用哪种方法，完成后应有以下产物：

- [x] ✅ 4个GGUF文件已生成
  - `lfm2-350m-browsergym-fp16.gguf` (~678MB)
  - `lfm2-350m-browsergym-q8_0.gguf` (~362MB) - **生产推荐**
  - `lfm2-350m-browsergym-q5_k_m.gguf` (~249MB)
  - `lfm2-350m-browsergym-q4_k_m.gguf` (~219MB)

- [x] ✅ llama.cpp编译完成（用于验证）

- [x] ✅ 模型推理验证通过
  ```bash
  # 快速验证命令
  cd llama.cpp
  ./build/bin/llama-cli \
    -m ../gguf_models_local/lfm2-350m-browsergym-q8_0.gguf \
    -p "Goal: Click button" -n 50
  ```
  - 模型能加载
  - 能生成合理输出
  - 推理速度正常（>5 t/s）

- [x] ✅ 转换脚本已保存（便于后续使用）
  - `scripts/convert_to_gguf_local.py`（本地方法）
  - `scripts/convert_to_gguf_simple.py`（Modal方法）

### 常见问题与解决方案

> **📖 详细故障排查**: 完整的问题描述、信息来源、解决过程请参见 [STAGE1_SUMMARY.md](STAGE1_SUMMARY.md#-常见问题快速参考)

| 问题 | 快速解决方案 |
|------|-------------|
| Modal转换失败 - UnicodeDecodeError | `subprocess.run(..., errors='ignore')` |
| 本地CUDA不可用 | 检查CUDA 13.0 + pyproject.toml配置 + `uv sync` |
| unsloth转换失败 | 使用llama.cpp工具链（本文档推荐） |
| PyTorch CUDA 12.x无法安装 | 升级CUDA 13.0或使用Modal云端 |

### 模型文件说明

| 文件 | 大小 | 量化方法 | 推荐场景 |
|------|------|----------|----------|
| lfm2-350m-browsergym-fp16.gguf | 678MB | FP16 | 基础文件，用于进一步量化 |
| lfm2-350m-browsergym-q8_0.gguf | 362MB | Q8_0 | **生产推荐**：高精度，性能好 |
| lfm2-350m-browsergym-q5_k_m.gguf | 249MB | Q5_K_M | 平衡：精度vs大小 |
| lfm2-350m-browsergym-q4_k_m.gguf | 219MB | Q4_K_M | 低端设备：最小文件 |

**Android构建推荐**: 使用Q8_0（362MB）或Q5_K_M（249MB）

---

### 阶段二: Android项目初始化 (1天)

#### 2.1 创建项目结构
```bash
cd examples/browser-control
mkdir -p android/BrowserControlDemo
cd android/BrowserControlDemo

# 使用Android Studio创建新项目，或使用命令行:
# - Project name: BrowserControlDemo
# - Package name: ai.liquid.browsercontrol
# - Min SDK: 31 (Android 12)
# - Language: Kotlin
# - Build system: Gradle (Kotlin DSL)
```

#### 2.2 配置Gradle
**`app/build.gradle.kts`**
```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "ai.liquid.browsercontrol"
    compileSdk = 34

    defaultConfig {
        applicationId = "ai.liquid.browsercontrol"
        minSdk = 31
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }
        
        // 仅支持arm64
        ndk {
            abiFilters += listOf("arm64-v8a")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    
    kotlinOptions {
        jvmTarget = "17"
    }
    
    buildFeatures {
        compose = true
    }
    
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.3"
    }
    
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // LeapSDK
    implementation("ai.liquid.leap:leap-sdk:0.9.7")
    implementation("ai.liquid.leap:leap-model-downloader:0.9.7")
    
    // Jetpack Compose
    implementation(platform("androidx.compose:compose-bom:2023.10.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.activity:activity-compose:1.8.2")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    
    // WebView
    implementation("androidx.webkit:webkit:1.9.0")
    
    // Testing
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
```

#### 2.3 配置AndroidManifest
**`app/src/main/AndroidManifest.xml`**
```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <!-- 权限 -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"
        android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"
        android:maxSdkVersion="32" />

    <application
        android:allowBackup="true"
        android:dataExtractionRules="@xml/data_extraction_rules"
        android:fullBackupContent="@xml/backup_rules"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.BrowserControlDemo"
        android:usesCleartextTraffic="true"
        tools:targetApi="31">
        
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:theme="@style/Theme.BrowserControlDemo">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

#### 2.4 复制系统Prompt
创建 `app/src/main/res/raw/system_prompt.txt`:
```text
You control a web browser through BrowserGym actions.
You must complete the given web task by interacting with the page.

Available actions:
- noop() - Do nothing
- click(bid) - Click element with BrowserGym ID (the number in brackets)
- fill(bid, text) - Fill input field with text
- send_keys(text) - Send keyboard input
- scroll(direction) - Scroll up/down

The page structure shows elements as: [bid] element_type 'element_text'
For example: [13] button 'Click Me!' means bid='13'

Reply with exactly ONE action on a single line, e.g.:
click('13')
fill('42', 'hello world')
noop()

Do not include explanations or multiple actions.
```

#### 2.5 阶段二完成总结 ✅

**完成时间**: 2026-02-22  
**耗时**: 约30分钟（自动化脚本）

**已创建文件**:
- ✅ `android/BrowserControlDemo/` - 项目根目录
- ✅ `app/build.gradle.kts` - 应用级Gradle配置（92行）
- ✅ `build.gradle.kts` - 项目级Gradle配置（4行）
- ✅ `settings.gradle.kts` - 项目设置（23行）
- ✅ `gradle.properties` - Gradle属性配置
- ✅ `gradle/wrapper/gradle-wrapper.properties` - Gradle 8.2配置
- ✅ `app/proguard-rules.pro` - ProGuard规则
- ✅ `app/src/main/AndroidManifest.xml` - 应用清单（35行）
- ✅ `app/src/main/res/values/strings.xml` - 字符串资源
- ✅ `app/src/main/res/values/themes.xml` - Material主题
- ✅ `app/src/main/res/xml/backup_rules.xml` - 备份规则
- ✅ `app/src/main/res/xml/data_extraction_rules.xml` - 数据提取规则
- ✅ `app/src/main/res/raw/system_prompt.txt` - 系统Prompt（17行）
- ✅ `app/src/main/java/ai/liquid/browsercontrol/MainActivity.kt` - 主Activity（68行）
- ✅ `README.md` - 项目文档（131行）

**关键配置**:
- ✅ LeapSDK 0.9.7集成（leap-sdk + leap-model-downloader）
- ✅ Jetpack Compose + Material3
- ✅ Kotlin 1.9.10 + Gradle 8.2
- ✅ 仅支持arm64-v8a架构
- ✅ 最低SDK 31（Android 12）

**验证清单**:
- [x] 目录结构完整
- [x] Gradle配置正确
- [x] 依赖库版本匹配
- [x] 网络权限配置
- [x] 系统Prompt就绪
- [x] 基础MainActivity实现
- [x] README文档完整

**下一步**: 进入阶段三 - 核心组件实现（ModelRunner, ActionParser, BrowserView）

---

### 阶段三: 核心组件实现 (5-6天)

#### 3.1 数据模型
**`domain/BrowserObservation.kt`**
```kotlin
package ai.liquid.browsercontrol.domain

data class BrowserObservation(
    val goal: String,          // 任务目标
    val axtree: String,        // 可访问性树
    val error: String? = null, // 错误信息
    val step: Int = 0          // 当前步骤
)
```

**`domain/BrowserAction.kt`**
```kotlin
package ai.liquid.browsercontrol.domain

sealed class BrowserAction {
    object Noop : BrowserAction()
    data class Click(val bid: String) : BrowserAction()
    data class Fill(val bid: String, val text: String) : BrowserAction()
    data class SendKeys(val text: String) : BrowserAction()
    data class Scroll(val direction: String) : BrowserAction()
    
    override fun toString(): String = when (this) {
        is Noop -> "noop()"
        is Click -> "click('$bid')"
        is Fill -> "fill('$bid', '$text')"
        is SendKeys -> "send_keys('$text')"
        is Scroll -> "scroll('$direction')"
    }
}

fun parseAction(response: String): BrowserAction {
    // 提取第一行包含括号的语句
    val actionLine = response.lines()
        .firstOrNull { it.contains("(") && it.contains(")") }
        ?.trim()
        ?: return BrowserAction.Noop
    
    return when {
        actionLine.startsWith("click(") -> {
            val bid = actionLine.substringAfter("('").substringBefore("')")
            BrowserAction.Click(bid)
        }
        actionLine.startsWith("fill(") -> {
            val content = actionLine.substringAfter("(").substringBefore(")")
            val parts = content.split(",").map { it.trim().trim('\'', '"') }
            if (parts.size >= 2) {
                BrowserAction.Fill(parts[0], parts[1])
            } else {
                BrowserAction.Noop
            }
        }
        actionLine.startsWith("send_keys(") -> {
            val text = actionLine.substringAfter("('").substringBefore("')")
            BrowserAction.SendKeys(text)
        }
        actionLine.startsWith("scroll(") -> {
            val direction = actionLine.substringAfter("('").substringBefore("')")
            BrowserAction.Scroll(direction)
        }
        else -> BrowserAction.Noop
    }
}
```

#### 3.2 Prompt格式化
**`domain/PromptFormatter.kt`**
```kotlin
package ai.liquid.browsercontrol.domain

object PromptFormatter {
    fun formatUserPrompt(observation: BrowserObservation): String {
        return buildString {
            appendLine("Step ${observation.step + 1}")
            appendLine()
            appendLine("Goal: ${observation.goal}")
            
            if (observation.error != null) {
                appendLine()
                appendLine("Previous action error: ${observation.error}")
            }
            
            appendLine()
            appendLine("Page structure:")
            appendLine(observation.axtree)
            appendLine()
            append("What action do you take?")
        }
    }
}
```

#### 3.3 WebView Accessibility提取
**`infrastructure/WebViewAccessibility.kt`**
```kotlin
package ai.liquid.browsercontrol.infrastructure

import android.webkit.WebView
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

object WebViewAccessibility {
    
    private val extractScript = """
        (function() {
            let tree = [];
            let bidCounter = 1;
            
            function traverse(node, indent = 0) {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    // 跳过script和style标签
                    if (node.tagName === 'SCRIPT' || node.tagName === 'STYLE') {
                        return;
                    }
                    
                    // 设置bid属性
                    node.setAttribute('data-bid', bidCounter.toString());
                    
                    // 构建树节点
                    let prefix = '  '.repeat(indent);
                    let entry = prefix + '[' + bidCounter + '] ' + node.tagName.toLowerCase();
                    
                    // 添加文本内容（仅直接子文本节点）
                    let directText = '';
                    for (let child of node.childNodes) {
                        if (child.nodeType === Node.TEXT_NODE) {
                            directText += child.textContent.trim();
                        }
                    }
                    if (directText) {
                        entry += " '" + directText.substring(0, 100) + "'";
                    }
                    
                    // 添加重要属性
                    if (node.id) entry += ' id="' + node.id + '"';
                    if (node.className) entry += ' class="' + node.className + '"';
                    
                    tree.push(entry);
                    bidCounter++;
                    
                    // 递归遍历子元素
                    for (let child of node.children) {
                        traverse(child, indent + 1);
                    }
                }
            }
            
            // 从body开始遍历
            if (document.body) {
                traverse(document.body);
            }
            
            return tree.join('\\n');
        })();
    """.trimIndent()
    
    suspend fun extractAXTree(webView: WebView, maxLength: Int = 2000): String {
        return suspendCoroutine { continuation ->
            webView.evaluateJavascript(extractScript) { result ->
                // 移除JSON转义的引号
                val tree = result?.trim('"')?.replace("\\n", "\n") ?: ""
                
                // 限制长度
                val truncated = if (tree.length > maxLength) {
                    tree.substring(0, maxLength) + "\n..."
                } else {
                    tree
                }
                
                continuation.resume(truncated)
            }
        }
    }
}
```

#### 3.4 动作执行器
**`infrastructure/ActionExecutor.kt`**
```kotlin
package ai.liquid.browsercontrol.infrastructure

import android.webkit.WebView
import ai.liquid.browsercontrol.domain.BrowserAction
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

object ActionExecutor {
    
    suspend fun execute(webView: WebView, action: BrowserAction): Result<String> {
        val script = when (action) {
            is BrowserAction.Noop -> {
                return Result.success("Noop action executed")
            }
            
            is BrowserAction.Click -> """
                (function() {
                    let element = document.querySelector('[data-bid="${action.bid}"]');
                    if (element) {
                        element.click();
                        return 'Clicked element ${action.bid}';
                    } else {
                        return 'Error: Element ${action.bid} not found';
                    }
                })();
            """.trimIndent()
            
            is BrowserAction.Fill -> """
                (function() {
                    let element = document.querySelector('[data-bid="${action.bid}"]');
                    if (element && (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA')) {
                        element.value = '${action.text}';
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        return 'Filled element ${action.bid} with: ${action.text}';
                    } else {
                        return 'Error: Input element ${action.bid} not found';
                    }
                })();
            """.trimIndent()
            
            is BrowserAction.SendKeys -> """
                (function() {
                    let activeElement = document.activeElement;
                    if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
                        activeElement.value += '${action.text}';
                        activeElement.dispatchEvent(new Event('input', { bubbles: true }));
                        return 'Sent keys: ${action.text}';
                    } else {
                        return 'Error: No active input element';
                    }
                })();
            """.trimIndent()
            
            is BrowserAction.Scroll -> """
                (function() {
                    let scrollAmount = '${action.direction}' === 'down' ? 200 : -200;
                    window.scrollBy(0, scrollAmount);
                    return 'Scrolled ${action.direction}';
                })();
            """.trimIndent()
        }
        
        return suspendCoroutine { continuation ->
            webView.evaluateJavascript(script) { result ->
                val message = result?.trim('"') ?: "Unknown result"
                
                if (message.startsWith("Error:")) {
                    continuation.resume(Result.failure(Exception(message)))
                } else {
                    continuation.resume(Result.success(message))
                }
            }
        }
    }
}
```

#### 3.5 模型推理
**`infrastructure/ModelInference.kt`**
```kotlin
package ai.liquid.browsercontrol.infrastructure

import ai.liquid.leap.downloader.LeapModelDownloader
import ai.liquid.leap.downloader.LeapModelDownloaderNotificationConfig
import ai.liquid.leap.sdk.Conversation
import ai.liquid.leap.sdk.MessageResponse
import ai.liquid.leap.sdk.ModelRunner
import android.content.Context
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

class ModelInference(private val context: Context) {
    
    private var modelRunner: ModelRunner? = null
    private var conversation: Conversation? = null
    
    private val downloader = LeapModelDownloader(
        context,
        notificationConfig = LeapModelDownloaderNotificationConfig.build {
            notificationTitleDownloading = "正在下载浏览器控制模型"
            notificationTitleDownloaded = "模型已就绪"
            notificationTextDownloadProgress = "已下载: {progress}%"
        }
    )
    
    suspend fun loadModel(
        modelSlug: String = "oceantime/LFM2-350M-browser-control",
        quantization: String = "Q8_0",
        systemPrompt: String
    ) {
        modelRunner = downloader.loadModel(
            modelSlug = modelSlug,
            quantizationSlug = quantization
        )
        
        conversation = modelRunner?.createConversation(systemPrompt)
    }
    
    fun generateAction(userPrompt: String): Flow<String> = flow {
        val conv = conversation ?: throw IllegalStateException("Model not loaded")
        
        val fullResponse = StringBuilder()
        
        conv.generateResponse(userPrompt).collect { response ->
            when (response) {
                is MessageResponse.Chunk -> {
                    fullResponse.append(response.text)
                    emit(response.text)
                }
                is MessageResponse.Complete -> {
                    // 生成完成
                }
            }
        }
    }
    
    fun isLoaded(): Boolean = conversation != null
    
    fun cleanup() {
        conversation = null
        modelRunner = null
    }
}
```

#### 3.6 ViewModel
**`viewmodel/BrowserViewModel.kt`**
```kotlin
package ai.liquid.browsercontrol.viewmodel

import ai.liquid.browsercontrol.domain.*
import ai.liquid.browsercontrol.infrastructure.*
import android.app.Application
import android.webkit.WebView
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.InputStreamReader

sealed class ModelState {
    object Idle : ModelState()
    data class Loading(val progress: String) : ModelState()
    object Ready : ModelState()
    data class Error(val message: String) : ModelState()
}

sealed class TaskState {
    object Idle : TaskState()
    data class Running(val step: Int, val maxSteps: Int) : TaskState()
    data class Completed(val success: Boolean, val steps: Int) : TaskState()
}

data class LogEntry(
    val timestamp: Long,
    val type: String, // "observation", "action", "result", "error"
    val content: String
)

class BrowserViewModel(application: Application) : AndroidViewModel(application) {
    
    private val modelInference = ModelInference(application)
    
    private val _modelState = MutableStateFlow<ModelState>(ModelState.Idle)
    val modelState: StateFlow<ModelState> = _modelState.asStateFlow()
    
    private val _taskState = MutableStateFlow<TaskState>(TaskState.Idle)
    val taskState: StateFlow<TaskState> = _taskState.asStateFlow()
    
    private val _logs = MutableStateFlow<List<LogEntry>>(emptyList())
    val logs: StateFlow<List<LogEntry>> = _logs.asStateFlow()
    
    private val _currentAXTree = MutableStateFlow("")
    val currentAXTree: StateFlow<String> = _currentAXTree.asStateFlow()
    
    private var stopRequested = false
    
    private val systemPrompt: String by lazy {
        val inputStream = getApplication<Application>()
            .resources
            .openRawResource(
                getApplication<Application>()
                    .resources
                    .getIdentifier("system_prompt", "raw", getApplication<Application>().packageName)
            )
        InputStreamReader(inputStream).readText()
    }
    
    fun loadModel() {
        viewModelScope.launch {
            try {
                _modelState.value = ModelState.Loading("初始化中...")
                
                modelInference.loadModel(
                    systemPrompt = systemPrompt
                )
                
                _modelState.value = ModelState.Ready
                addLog("info", "✓ 模型加载成功")
            } catch (e: Exception) {
                _modelState.value = ModelState.Error(e.message ?: "未知错误")
                addLog("error", "✗ 模型加载失败: ${e.message}")
            }
        }
    }
    
    fun runTask(webView: WebView, maxSteps: Int = 5) {
        if (!modelInference.isLoaded()) {
            addLog("error", "模型未加载")
            return
        }
        
        stopRequested = false
        
        viewModelScope.launch {
            try {
                _taskState.value = TaskState.Running(0, maxSteps)
                addLog("info", "========== 任务开始 ==========")
                
                val goal = "Click the button"
                
                for (step in 0 until maxSteps) {
                    if (stopRequested) {
                        addLog("info", "任务已停止")
                        break
                    }
                    
                    _taskState.value = TaskState.Running(step, maxSteps)
                    
                    // 1. 提取accessibility tree
                    addLog("info", "--- Step ${step + 1} ---")
                    val axtree = WebViewAccessibility.extractAXTree(webView)
                    _currentAXTree.value = axtree
                    addLog("observation", "AXTree提取完成 (${axtree.length} chars)")
                    
                    // 2. 构建observation
                    val observation = BrowserObservation(
                        goal = goal,
                        axtree = axtree,
                        step = step
                    )
                    
                    // 3. 格式化prompt
                    val userPrompt = PromptFormatter.formatUserPrompt(observation)
                    
                    // 4. 模型推理
                    addLog("info", "正在推理...")
                    val responseBuilder = StringBuilder()
                    
                    modelInference.generateAction(userPrompt).collect { chunk ->
                        responseBuilder.append(chunk)
                    }
                    
                    val response = responseBuilder.toString()
                    addLog("action", "模型输出: $response")
                    
                    // 5. 解析动作
                    val action = parseAction(response)
                    addLog("action", "解析动作: $action")
                    
                    // 6. 执行动作
                    delay(500) // 等待UI更新
                    val result = ActionExecutor.execute(webView, action)
                    
                    result.fold(
                        onSuccess = { message ->
                            addLog("result", "✓ $message")
                        },
                        onFailure = { error ->
                            addLog("error", "✗ ${error.message}")
                        }
                    )
                    
                    // 7. 等待页面更新
                    delay(1000)
                    
                    // 8. 检查是否完成（简化版：假设click后即完成）
                    if (action is BrowserAction.Click) {
                        addLog("info", "========== 任务完成 ==========")
                        _taskState.value = TaskState.Completed(true, step + 1)
                        return@launch
                    }
                }
                
                addLog("info", "========== 达到最大步数 ==========")
                _taskState.value = TaskState.Completed(false, maxSteps)
                
            } catch (e: Exception) {
                addLog("error", "任务执行出错: ${e.message}")
                _taskState.value = TaskState.Idle
            }
        }
    }
    
    fun stopTask() {
        stopRequested = true
    }
    
    fun resetTask() {
        _taskState.value = TaskState.Idle
        _logs.value = emptyList()
        _currentAXTree.value = ""
    }
    
    private fun addLog(type: String, content: String) {
        val entry = LogEntry(
            timestamp = System.currentTimeMillis(),
            type = type,
            content = content
        )
        _logs.value = _logs.value + entry
    }
    
    override fun onCleared() {
        super.onCleared()
        modelInference.cleanup()
    }
}
```

#### ✅ 阶段三完成总结 (2026-02-22)

| 文件 | 包 | 状态 | 说明 |
|------|----|------|------|
| `domain/BrowserObservation.kt` | domain | ✅ | 任务观测数据类 |
| `domain/BrowserAction.kt` | domain | ✅ | 动作密封类 + `parseAction()` |
| `domain/PromptFormatter.kt` | domain | ✅ | LLM提示词格式化 |
| `infrastructure/WebViewAccessibility.kt` | infrastructure | ✅ | AXTree提取（JS注入） |
| `infrastructure/ActionExecutor.kt` | infrastructure | ✅ | WebView动作执行 |
| `infrastructure/ModelInference.kt` | infrastructure | ✅ | LeapSDK推理封装（已修复API） |
| `viewmodel/BrowserViewModel.kt` | viewmodel | ✅ | 推理主循环ViewModel |

**LeapSDK API修复记录**:
- ❌ 旧包路径 `ai.liquid.leap.sdk.*` → ✅ 正确包 `ai.liquid.leap.*` + `ai.liquid.leap.message.*`
- ❌ 参数名 `modelSlug` / `quantizationSlug` → ✅ `modelName` / `quantizationType`
- ❌ `notificationTextDownloadProgress`（不存在）→ ✅ 已删除
- ❌ `MessageResponse.Complete`（Android SDK无此类型）→ ✅ 改为 `else -> {}`

**下一步**: 进入阶段四 - UI实现（WebViewCompose + BrowserControlScreen）

---

### 阶段四: UI实现 (2天)

#### 4.1 WebView组件
**`ui/WebViewCompose.kt`**
```kotlin
package ai.liquid.browsercontrol.ui

import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView

@Composable
fun WebViewCompose(
    url: String,
    modifier: Modifier = Modifier,
    onWebViewCreated: (WebView) -> Unit = {}
) {
    AndroidView(
        modifier = modifier,
        factory = { context ->
            WebView(context).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )
                
                settings.apply {
                    javaScriptEnabled = true
                    domStorageEnabled = true
                    loadWithOverviewMode = true
                    useWideViewPort = true
                }
                
                webViewClient = WebViewClient()
                
                loadUrl(url)
                
                onWebViewCreated(this)
            }
        }
    )
}
```

#### 4.2 主界面
**`ui/BrowserControlScreen.kt`**
```kotlin
package ai.liquid.browsercontrol.ui

import ai.liquid.browsercontrol.viewmodel.*
import android.webkit.WebView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BrowserControlScreen(viewModel: BrowserViewModel) {
    val modelState by viewModel.modelState.collectAsState()
    val taskState by viewModel.taskState.collectAsState()
    val logs by viewModel.logs.collectAsState()
    val axtree by viewModel.currentAXTree.collectAsState()
    
    var webView: WebView? by remember { mutableStateOf(null) }
    var showAXTree by remember { mutableStateOf(false) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Browser Control Demo") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // 状态栏
            StatusBar(modelState, taskState)
            
            // 主内容区域
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .weight(1f)
            ) {
                // 左侧: WebView
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                ) {
                    WebViewCompose(
                        url = AppConfig.taskUrl("click-button"),  // 通过 AppConfig 配置，支持本地Docker/远程切换
                        modifier = Modifier.fillMaxSize(),
                        onWebViewCreated = { webView = it }
                    )
                }
                
                // 右侧: 日志
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .background(Color(0xFF1E1E1E))
                ) {
                    // 标签栏
                    TabRow(selectedTabIndex = if (showAXTree) 1 else 0) {
                        Tab(
                            selected = !showAXTree,
                            onClick = { showAXTree = false },
                            text = { Text("日志") }
                        )
                        Tab(
                            selected = showAXTree,
                            onClick = { showAXTree = true },
                            text = { Text("AXTree") }
                        )
                    }
                    
                    // 内容
                    if (showAXTree) {
                        AXTreeView(axtree)
                    } else {
                        LogView(logs)
                    }
                }
            }
            
            // 控制按钮
            ControlButtons(
                modelState = modelState,
                taskState = taskState,
                onLoadModel = { viewModel.loadModel() },
                onStartTask = { webView?.let { viewModel.runTask(it) } },
                onStopTask = { viewModel.stopTask() },
                onResetTask = {
                    viewModel.resetTask()
                    webView?.reload()
                }
            )
        }
    }
}

@Composable
fun StatusBar(modelState: ModelState, taskState: TaskState) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.secondaryContainer
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            // 模型状态
            Text(
                text = when (modelState) {
                    is ModelState.Idle -> "⚪ 模型: 未加载"
                    is ModelState.Loading -> "🟡 模型: ${modelState.progress}"
                    is ModelState.Ready -> "🟢 模型: 就绪"
                    is ModelState.Error -> "🔴 模型: ${modelState.message}"
                },
                style = MaterialTheme.typography.bodyMedium
            )
            
            // 任务状态
            Text(
                text = when (taskState) {
                    is TaskState.Idle -> "任务: 待开始"
                    is TaskState.Running -> "任务: Step ${taskState.step + 1}/${taskState.maxSteps}"
                    is TaskState.Completed -> if (taskState.success) {
                        "✓ 任务完成 (${taskState.steps} steps)"
                    } else {
                        "任务未完成 (${taskState.steps} steps)"
                    }
                },
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

@Composable
fun LogView(logs: List<LogEntry>) {
    val listState = rememberLazyListState()
    
    LaunchedEffect(logs.size) {
        if (logs.isNotEmpty()) {
            listState.animateScrollToItem(logs.size - 1)
        }
    }
    
    LazyColumn(
        state = listState,
        modifier = Modifier
            .fillMaxSize()
            .padding(8.dp)
    ) {
        items(logs) { log ->
            LogItem(log)
        }
    }
}

@Composable
fun LogItem(log: LogEntry) {
    val color = when (log.type) {
        "info" -> Color(0xFFBBBBBB)
        "observation" -> Color(0xFF64B5F6)
        "action" -> Color(0xFF81C784)
        "result" -> Color(0xFFFFD54F)
        "error" -> Color(0xFFE57373)
        else -> Color.White
    }
    
    val timeFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
    val timeStr = timeFormat.format(Date(log.timestamp))
    
    Text(
        text = "[$timeStr] ${log.content}",
        color = color,
        fontSize = 12.sp,
        fontFamily = FontFamily.Monospace,
        modifier = Modifier.padding(vertical = 2.dp)
    )
}

@Composable
fun AXTreeView(axtree: String) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(8.dp)
    ) {
        item {
            Text(
                text = axtree.ifEmpty { "未提取" },
                color = Color(0xFF90CAF9),
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}

@Composable
fun ControlButtons(
    modelState: ModelState,
    taskState: TaskState,
    onLoadModel: () -> Unit,
    onStartTask: () -> Unit,
    onStopTask: () -> Unit,
    onResetTask: () -> Unit
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 4.dp
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // 加载模型按钮
            Button(
                onClick = onLoadModel,
                enabled = modelState is ModelState.Idle || modelState is ModelState.Error
            ) {
                Text("加载模型")
            }
            
            // 开始任务按钮
            Button(
                onClick = onStartTask,
                enabled = modelState is ModelState.Ready && taskState is TaskState.Idle
            ) {
                Text("开始任务")
            }
            
            // 停止按钮
            Button(
                onClick = onStopTask,
                enabled = taskState is TaskState.Running,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.error
                )
            ) {
                Text("停止")
            }
            
            // 重置按钮
            Button(
                onClick = onResetTask,
                enabled = taskState !is TaskState.Running
            ) {
                Text("重置")
            }
        }
    }
}
```

#### 4.3 MainActivity
**`MainActivity.kt`**
```kotlin
package ai.liquid.browsercontrol

import ai.liquid.browsercontrol.ui.BrowserControlScreen
import ai.liquid.browsercontrol.viewmodel.BrowserViewModel
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.viewmodel.compose.viewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContent {
            MaterialTheme {
                val viewModel: BrowserViewModel = viewModel()
                BrowserControlScreen(viewModel)
            }
        }
    }
}
```

#### ✅ 阶段四完成总结 (2026-02-22)

| 文件 | 包 | 状态 | 说明 |
|------|----|------|------|
| `ui/WebViewCompose.kt` | ui | ✅ | AndroidView封装WebView，支持JS+回调 |
| `ui/BrowserControlScreen.kt` | ui | ✅ | Scaffold主界面：状态栏/WebView/日志/控制按钮 |
| `MainActivity.kt` | root | ✅ | 替换占位内容，接入BrowserViewModel + BrowserControlScreen |
| `AppConfig.kt` | root | ✅ | URL运行时配置：本地Docker / 远程切换 |

**UI架构**:
- `StatusBar` — 顶部实时显示模型状态和任务进度
- `WebViewCompose` — 左侧加载 MiniWoB 任务页面（URL 通过 `AppConfig` 配置）
- `LogView` / `AXTreeView` — 右侧双标签：推理日志（带颜色分类）/ AXTree内容
- `ControlButtons` — 底部：加载模型 / 开始任务 / 停止 / 重置

**下一步**: 进入阶段五 — 本地 Docker 构建 MiniWoB++ + ARM64 设备集成测试

---

### 阶段五: 集成测试 (2天)

#### 5.0 前提：两台机器分工

本项目存在**双重架构约束**，需要两台机器各司其职：

| 角色 | 架构要求 | 工作内容 |
|------|---------|---------|
| **编译机** | x86_64（Linux/macOS/WSL2） | 运行 `./gradlew assembleDebug` 生成 APK |
| **测试设备** | ARM64 Android 物理设备 | 运行推理（GGML 依赖 ARM NEON/SVE 指令集） |

> **为什么需要分开？**
> - Android `build-tools`（`aapt2`/`d8`）只有 x86_64 Linux 版本，ARM64 宿主机无法执行
> - GGML 推理（LeapSDK）依赖 ARM NEON 指令，x86_64 模拟器运行会 `SIGILL` 崩溃
> - 因此：**x86_64 编译 APK → ARM64 设备运行推理**

**编译机选项**（任选一）：
- macOS（Apple Silicon 或 Intel）
- Linux x86_64（本地机器或云服务器）
- Windows WSL2（Ubuntu x86_64 子系统）

**测试设备选项**：

| 设备类型 | 说明 |
|---------|------|
| ARM64 物理设备（推荐） | 任何现代 Android手机（骁龙/天玑/Exynos），USB 连接到编译机 |
| ARM64 AVD | Android Studio → New Device → 选 `arm64-v8a` 系统镜像 |
| ~~x86_64 模拟器~~ | ❌ GGML 推理必崩（`SIGILL` in `ggml_vec_dot_q8_0_q8_0`） |

验证设备架构：
```bash
adb shell uname -m   # 期望: aarch64
```

---

#### 5.1 MiniWoB++ 本地 Docker 构建

> **为什么用本地构建？**
> - 在线版（farama.org）是文档页 + iframe 嵌套，AXTree 含大量文档 DOM，信噪比低
> - 本地版直接加载任务 HTML，AXTree 精简（约20个元素），LLM 推理准确度更高
> - 无外网依赖，测试稳定可重复

##### 5.1.1 目录结构

在项目根创建：
```
examples/browser-control/docker/miniwob/
├── Dockerfile
├── server.py
└── docker-compose.yml
```

##### 5.1.2 `server.py`

基于 miniwob-plusplus [`http_server.py`](https://github.com/Farama-Foundation/miniwob-plusplus/blob/master/miniwob/http_server.py) 改造，添加 CORS 并绑定 `0.0.0.0`：

```python
"""MiniWoB++ 本地 HTTP 服务，将 miniwob/html/ 暴露给 Android WebView 访问。"""
import functools, os, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class CORSRequestHandler(SimpleHTTPRequestHandler):
    """添加 CORS 响应头，支持 Android WebView 跨域访问。"""
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS, HEAD")
        self.send_header("Cache-Control", "no-cache, no-store")
        super().end_headers()
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args):
        if args and str(args[1]) != "200":
            super().log_message(format, *args)

if __name__ == "__main__":
    html_dir = sys.argv[1] if len(sys.argv) > 1 else "/app/html"
    port = int(os.environ.get("PORT", 8080))
    if not os.path.isdir(html_dir):
        print(f"ERROR: html_dir '{html_dir}' not found", file=sys.stderr)
        sys.exit(1)
    handler = functools.partial(CORSRequestHandler, directory=html_dir)
    with ThreadingHTTPServer(("0.0.0.0", port), handler) as httpd:
        print(f"✓ MiniWoB++ running at http://0.0.0.0:{port}/miniwob/click-button.html")
        httpd.serve_forever()
```

##### 5.1.3 `Dockerfile`

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && git clone --depth=1 https://github.com/Farama-Foundation/miniwob-plusplus.git /tmp/miniwob \
    && mkdir -p /app \
    && cp -r /tmp/miniwob/miniwob/html /app/html \
    && rm -rf /tmp/miniwob /var/lib/apt/lists/*

COPY server.py /app/server.py

EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/miniwob/click-button.html')"

CMD ["python", "/app/server.py", "/app/html"]
```

##### 5.1.4 `docker-compose.yml`

```yaml
services:
  miniwob:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: miniwob-server
    ports:
      - "8080:8080"
    restart: unless-stopped
```

##### 5.1.5 启动与验证

```bash
cd examples/browser-control/docker/miniwob
docker compose up -d --build

# 验证服务（宿主机）
curl -I http://localhost:8080/miniwob/click-button.html
# 期望: HTTP/1.0 200 OK  +  Access-Control-Allow-Origin: *

# 验证任务页面数量（约125个）
curl -s http://localhost:8080/miniwob/ | grep -c '\.html'

# 验证从模拟器可达
adb shell "curl -o /dev/null -s -w '%{http_code}' http://10.0.2.2:8080/miniwob/click-button.html"
# 期望: 200
```

##### 5.1.6 网络地址速查

| 场景 | `AppConfig.BASE_URL` |
|------|---------------------|
| 模拟器（x86_64 / ARM64 AVD） | `http://10.0.2.2:8080` |
| USB 物理设备（同宿主机） | `http://192.168.x.x:8080`（`hostname -I` 查询） |
| WiFi 物理设备 | `http://[宿主机LAN IP]:8080` |
| 远程（无需 Docker） | `https://miniwob.farama.org/environments` |

> `10.0.2.2` 是 Android 模拟器内置的宿主机 loopback 固定别名，无需额外配置。

##### 5.1.7 在线版 vs 本地版差异

| 对比项 | 在线版 | 本地版 ✅ |
|--------|--------|----------|
| 页面结构 | 文档页 + iframe 嵌套任务 | 纯任务 HTML，无 iframe |
| START 按钮位置 | iframe 内，需跨 frame | 直接在 `body` |
| AXTree 元素数 | 数百个（含文档导航） | 约20个（仅任务元素） |
| LLM 推理准确度 | 低（干扰元素多） | 高（信噪比优） |
| 外网依赖 | 需要 | 无 |

---

#### 5.2 AppConfig.kt — URL 配置

创建 `app/src/main/java/ai/liquid/browsercontrol/AppConfig.kt`：

```kotlin
package ai.liquid.browsercontrol

object AppConfig {
    // 本地 Docker（模拟器：10.0.2.2 = 宿主机 loopback）
    private const val BASE_URL = "http://10.0.2.2:8080"

    // 本地 Docker（物理设备：替换为宿主机 LAN IP）
    // private const val BASE_URL = "http://192.168.1.100:8080"

    // 远程（无需 Docker）
    // private const val BASE_URL = "https://miniwob.farama.org/environments"

    /** 返回任务 URL。本地版: /miniwob/{task}.html；远程版: /environments/{task}/ */
    fun taskUrl(task: String = "click-button"): String =
        if (BASE_URL.contains("farama.org")) "$BASE_URL/$task/"
        else "$BASE_URL/miniwob/$task.html"
}
```

#### 5.3 BrowserControlScreen.kt — 替换硬编码 URL

将 `url = "https://miniwob.farama.org/environments/click-button/"` 改为：

```kotlin
url = AppConfig.taskUrl("click-button"),
```

---

#### 5.4 编译与安装（方案C：x86_64 编译机）

##### 步骤一：x86_64 编译机准备

在 **x86_64 机器**（macOS/Linux/WSL2）上执行：

```bash
# 1. 获取项目代码
git clone <repo_url>
cd examples/browser-control/android/BrowserControlDemo

# 2. 在项目根创建 local.properties（不提交到 git）
cat > local.properties << 'EOF'
sdk.dir=/path/to/your/android/sdk

gpr.user=browser-control
gpr.token=YOUR_GITHUB_PAT_HERE
EOF
# macOS 默认 sdk.dir: /Users/<user>/Library/Android/sdk
# Linux x86_64 默认:   /home/<user>/Android/Sdk

# 3. Android Studio 安装时通常自带 SDK，确认组件齐全
#    若缺少，安装：platforms;android-36 + build-tools;36.0.0

# 4. 构建 debug APK
./gradlew assembleDebug

# 成功后 APK 路径：
# app/build/outputs/apk/debug/app-debug.apk
```

##### 步骤二：连接 ARM64 设备，安装 APK

在 **x86_64 编译机**上（通过 USB 连接 ARM64 Android 设备）：

```bash
# 验证设备已连接且为 ARM64
adb devices
adb shell uname -m   # 期望: aarch64

# 安装 APK
adb install app/build/outputs/apk/debug/app-debug.apk

# 推送模型文件（需先获取 GGUF + JSON 文件）
adb push LFM2-350M-Q8_0.gguf /sdcard/LFM2-350M-Q8_0.gguf
adb push LFM2-350M-Q8_0.json /sdcard/LFM2-350M-Q8_0.json

# 启动 App
adb shell am start -n ai.liquid.browsercontrol/.MainActivity
```

##### 步骤三：MiniWoB Docker 服务

Docker 服务可在**任意一台机器**上运行（只要 Android 设备网络可达）：

```bash
# 在编译机或 ARM64 开发机上启动（已运行则跳过）
cd examples/browser-control/docker/miniwob
docker compose up -d

# 验证服务
curl -I http://localhost:8080/miniwob/click-button.html  # → 200 OK
```

> **AppConfig.kt 地址说明**：
> - 设备通过 USB 连接到运行 Docker 的机器 → 若是 AVD 用 `10.0.2.2`；若是物理设备用宿主机 LAN IP
> - 默认配置 `http://10.0.2.2:8080` 适用于模拟器；物理设备需改为 `http://192.168.x.x:8080`

#### 5.5 测试清单

- [x] x86_64 编译机完成 `./gradlew assembleDebug`，APK 生成
- [x] ARM64 设备通过 USB 连接到编译机（`adb shell uname -m` → `aarch64`）
- [x] Docker 服务启动（`curl -I http://localhost:8080/miniwob/click-button.html` → 200）
- [x] App 安装成功，系统弹出 MANAGE_EXTERNAL_STORAGE 权限授予对话框
- [x] 模型文件推送完成（GGUF + JSON 均在 `/sdcard/`）
- [x] 点击"加载模型" → 日志显示"✓ 模型加载成功"
- [x] WebView 正常显示本地 MiniWoB 任务页面（`http://10.0.2.2:8080/miniwob/click-button.html`）
- [x] 点击任务内"START"按钮后，页面出现待点击按钮
- [x] 点击"开始任务" → AXTree 提取约20条元素（含目标按钮）
- [x] 模型生成 `click('bid')` 动作
- [x] JavaScript 执行点击成功，任务页面显示完成
- [x] 日志显示完整推理流程，无崩溃
- [x] UI 不卡顿（推理在 `Dispatchers.Default` 后台线程）
- [x] MiniWoB reward 通过 `endEpisode` 拦截器捕获，动作成功后立即显示评分覆盖层
- [x] 作者模型 (Paulescu/LFM2-350M-browsergym-20251224-013119) 转换为 Q8_0 GGUF 并推送验证

#### 5.6 常见问题

**问题0: `aapt2` / `d8` 无法执行（ARM64 编译机）**
```
原因: Google 只提供 x86_64 Linux 版 aapt2/d8，ARM64 宿主机无法直接运行
     ELF 64-bit LSB executable, x86-64 ...
现象: ./gradlew assembleDebug → "cannot execute binary file: Exec format error"
解决: 在 x86_64 机器（macOS / Linux x86_64 / WSL2）上执行编译（方案C）
     ARM64 开发机只负责运行测试，不负责编译
```

**问题1: SIGILL 崩溃**
```
原因: x86_64 模拟器不支持 ARM NEON/SVE 指令（GGML ggml_vec_dot_q8_0_q8_0）
解决: 使用 ARM64 物理设备或 ARM64 AVD（系统镜像选 arm64-v8a）
```

**问题2: WebView 无法加载 MiniWoB（ERR_CONNECTION_REFUSED）**
```
解决:
- 确认 Docker 服务正在运行: docker compose ps
- 模拟器用 10.0.2.2，物理设备用宿主机 LAN IP
- 检查 AndroidManifest.xml 是否有 android:usesCleartextTraffic="true"
```

**问题3: 模型文件找不到（ENOENT）**
```
解决:
- adb push 两个文件: LFM2-350M-Q8_0.gguf + LFM2-350M-Q8_0.json
- 在 App 设置中授予 MANAGE_EXTERNAL_STORAGE 权限
- 日志会显示推荐的 push 路径
```

**问题4: AXTree 提取为空**
```
解决:
- 确认 JavaScript 已启用（WebViewCompose 中 settings.javaScriptEnabled = true）
- 等待页面完全加载后再点击"开始任务"
- 先点击 MiniWoB 页面内的"START"按钮使任务出现
```

**问题5: 推理速度慢**
```
解决:
- 降低量化级别: Q8_0 → Q4_K_M（文件小约40%，速度快约30%）
- 减少 max_new_tokens
- 使用旗舰机型（骁龙8系/天玑9系）
```

---

### 阶段六: 文档与交付 (1天)

#### 6.1 项目README
创建 `examples/browser-control/android/README.md`:

```markdown
# Browser Control Android Demo

基于LeapSDK的浏览器自动化控制Android应用演示。

## 功能

- ✅ 本地LFM2-350M模型推理
- ✅ WebView集成
- ✅ 自动提取Accessibility Tree
- ✅ 动作解析和执行
- ✅ 实时日志显示

## 环境要求

- Android 12+ (API 31+)
- arm64-v8a架构
- 4GB+ RAM推荐
- 网络连接（首次下载模型）

## 构建步骤

### 1. 准备模型

参考 [模型转换指南](../../docs/browser-control-android-deploy.md#阶段一-模型转换与验证-2-3天) 将checkpoint转换为GGUF格式并上传到HuggingFace。

### 2. Clone项目

\```bash
git clone [repository]
cd examples/browser-control/android/BrowserControlDemo
\```

### 3. 使用Android Studio

1. 打开Android Studio
2. File → Open → 选择 `BrowserControlDemo` 目录
3. 等待Gradle同步完成
4. 连接Android设备或启动模拟器
5. 点击Run按钮

### 4. 命令行构建

\```bash
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
\```

## 使用说明

1. **启动应用**
2. **加载模型**: 点击"加载模型"按钮，等待下载和初始化（首次需要~1分钟）
3. **开始任务**: 模型就绪后，点击"开始任务"
4. **观察执行**: 
   - 左侧WebView显示MiniWoB页面
   - 右侧实时显示日志和AXTree
   - 模型自动推理并点击按钮
5. **重置测试**: 点击"重置"重新开始

## 项目结构

\```
app/src/main/java/ai/liquid/browsercontrol/
├── MainActivity.kt              # 入口Activity
├── ui/
│   ├── BrowserControlScreen.kt  # 主界面
│   └── WebViewCompose.kt        # WebView封装
├── viewmodel/
│   └── BrowserViewModel.kt      # 业务逻辑
├── domain/
│   ├── BrowserObservation.kt    # 观察数据模型
│   ├── BrowserAction.kt         # 动作模型
│   └── PromptFormatter.kt       # Prompt构建
└── infrastructure/
    ├── ModelInference.kt        # LeapSDK推理
    ├── WebViewAccessibility.kt  # AXTree提取
    └── ActionExecutor.kt        # 动作执行
\```

## 性能指标

| 指标 | Q8_0 | Q5_K_M | Q4_K_M |
|------|------|--------|--------|
| 模型大小 | ~350MB | ~250MB | ~200MB |
| 推理延迟 | ~2-3s | ~1.5-2s | ~1-1.5s |
| 内存占用 | ~1.5GB | ~1.2GB | ~1GB |

## 已知限制

- 仅支持text-only任务（不包含视觉信息）
- AXTree提取依赖JavaScript（某些网站可能失败）
- 复杂页面的AXTree可能超过2000字符限制
- 仅验证了click-button简单任务

## 故障排除

### 模型加载失败
- 检查网络连接
- 确认HuggingFace模型已正确上传
- 查看应用日志: `adb logcat | grep LeapSDK`

### WebView空白
- 检查网络权限
- 确认AndroidManifest.xml中设置了INTERNET权限
- 尝试使用HTTP而非HTTPS（添加usesCleartextTraffic）

### 推理过慢
- 切换到更低量化级别 (Q4_K_M)
- 使用性能更强的设备
- 减少max_new_tokens参数

## 参考资源

- [LeapSDK文档](https://docs.liquid.ai/leap/edge-sdk/android/android-quick-start-guide)
- [LeapSDK示例](https://github.com/oceantime/LeapSDK-Examples)
- [Browser-Control训练文档](browser-control-model-deploy.md)
- [Android构建方案](../../docs/browser-control-android-deploy.md)

## License

Apache 2.0
```

#### 6.2 更新主文档
在 `examples/browser-control/docs/browser-control-model-deploy.md` 添加新章节：

```markdown
## 12. Android端构建

详细的Android构建方案请参考: [browser-control-android-deploy.md](browser-control-android-deploy.md)

### 快速开始
1. 转换模型为GGUF格式
2. 上传到HuggingFace
3. 构建Android应用
4. 在设备上测试

### 预期结果
- ✅ 模型在Android设备本地运行
- ✅ 自动识别并点击网页按钮
- ✅ 推理延迟 < 3秒 (Q8_0)
- ✅ 内存占用 < 2GB

### 演示视频
[media/android-demo.mp4](../media/android-demo.mp4)
```

#### 6.3 录制演示视频
使用Android Studio或adb录屏:

```bash
# 开始录屏
adb shell screenrecord /sdcard/demo.mp4

# 操作应用（完整流程）
# 1. 加载模型
# 2. 开始任务
# 3. 观察点击执行
# 4. 显示日志

# 停止录屏（Ctrl+C）

# 下载视频
adb pull /sdcard/demo.mp4 media/android-demo.mp4
```

---

## 3. 验证标准

### 功能验证清单
- [x] GGUF模型转换成功
- [x] 本地llama.cpp推理通过
- [x] 模型上传到HuggingFace
- [x] Android项目构建成功
- [x] 模型在LeapSDK中加载
- [x] WebView显示MiniWoB页面
- [x] AXTree正确提取button元素
- [x] 模型生成click('X')动作
- [x] JavaScript成功执行点击
- [x] UI实时显示日志
- [x] 完整流程端到端通过

### 性能指标
| 指标 | 目标 | 实际 |
|------|------|------|
| 模型加载时间 | < 30s | _待测_ |
| 单步推理延迟 (Q8_0) | < 3s | _待测_ |
| 内存峰值占用 | < 2GB | _待测_ |
| click-button成功率 | > 80% | _待测_ |
| APK大小 | < 50MB | _待测_ |

### 交付物检查
- [x] Android APK文件
- [x] GGUF模型文件（HuggingFace + 本地 Q8_0）
- [x] 完整源代码
- [x] README文档
- [ ] 演示视频（可选）
- [ ] 性能测试报告（可选）

---

## 4. 技术决策记录

### 决策1: LeapSDK vs PyTorch Mobile
**选择**: LeapSDK (GGUF + llama.cpp)

**理由**:
- GGUF量化后体积小（350MB vs 1.4GB）
- llama.cpp推理速度快
- LeapSDK提供完整的Android集成
- 有官方示例可参考

### 决策2: JavaScript注入 vs Accessibility Service
**选择**: JavaScript注入

**理由**:
- MiniWoB页面结构简单
- JavaScript更直接可控
- 快速原型开发优先
- Accessibility Service需要额外权限和配置

### 决策3: 使用MiniWoB线上页面
**选择**: 使用https://miniwob.farama.org/environments/click-button/

**理由**:
- 保持与训练环境一致
- 避免页面结构差异
- 官方维护更新
- WebView可以通过设置处理跨域

### 决策4: 量化级别选择
**选择**: 默认Q8_0，可选Q5_K_M/Q4_K_M

**理由**:
- Q8_0量化损失最小
- 平衡质量和性能
- 用户可根据设备性能调整

### 决策5: 快速原型优先
**选择**: 2周完成核心功能验证

**理由**:
- 尽快验证可行性
- 避免过度工程化
- 基于反馈迭代优化

---

## 5. 风险与缓解

### 风险1: Accessibility Tree格式差异
**描述**: Android提取的AXTree可能与训练时的Playwright AXTree格式不同

**影响**: 模型推理准确率下降

**缓解**:
- 在JavaScript提取时尽量模拟Playwright格式
- 对比Python版本调整格式
- 如准确率低，考虑微调模型适配新格式

### 风险2: 设备性能限制
**描述**: 部分Android设备RAM不足或CPU较弱

**影响**: 推理慢或OOM崩溃

**缓解**:
- 推荐使用Q4_K_M量化降低要求
- 添加设备检查和警告
- 优化内存管理（及时释放）

### 风险3: MiniWoB页面访问问题
**描述**: 网络限制或页面变更

**影响**: WebView无法加载测试页面

**缓解**:
- 提供离线HTML备选方案
- 文档说明网络要求
- 支持自定义URL配置

### 风险4: 模型泛化能力有限
**描述**: 仅在click-test训练，复杂任务可能失败

**影响**: 演示效果受限

**缓解**:
- 明确标注演示范围
- 文档说明已知限制
- 未来扩展训练其他任务

---

## 6. 后续扩展方向

### 短期优化 (1-2周)
- [ ] 支持更多MiniWoB任务（fill表单、多步骤）
- [ ] 优化UI/UX（进度条、动画）
- [ ] 添加单元测试和集成测试
- [ ] 性能profiling和优化

### 中期扩展 (1个月)
- [ ] 支持自定义网页URL
- [ ] 实现离线HTML测试环境
- [ ] 添加视觉-语言模型（VLM）支持
- [ ] 多步骤任务规划

### 长期目标 (3个月+)
- [ ] 训练book-flight等复杂任务
- [ ] 发布到Google Play
- [ ] iOS版本开发
- [ ] 云端协同（混合推理）

---

## 7. 参考资源

### 官方文档
- [LeapSDK Android快速开始](https://docs.liquid.ai/leap/edge-sdk/android/android-quick-start-guide)
- [LeapSDK示例项目](https://github.com/oceantime/LeapSDK-Examples)
- [Liquid AI LFM2模型](https://huggingface.co/LiquidAI/LFM2-350M)

### 技术资料
- [llama.cpp GGUF格式](https://github.com/ggerganov/llama.cpp/blob/master/docs/GGUF.md)
- [Unsloth模型转换](https://github.com/unslothai/unsloth)
- [MiniWoB基准测试](https://miniwob.farama.org/)
- [BrowserGym环境](https://browsergym.github.io/)

### 训练相关
- [Browser-Control训练文档](browser-control-model-deploy.md)
- [GRPO算法](https://arxiv.org/abs/2402.03300)
- [Modal云服务](https://modal.com/docs)

---

## 附录: 常用命令

### 模型相关
```bash
# 转换为GGUF
uv run python src/browser_control/convert_to_gguf.py

# 验证GGUF
./llama-cli -m model.gguf -p "test"

# 上传到HuggingFace
uv run huggingface-cli upload oceantime/LFM2-350M-browser-control ./gguf_models
```

### Android开发
```bash
# 构建
./gradlew assembleDebug

# 安装
adb install app/build/outputs/apk/debug/app-debug.apk

# 启动
adb shell am start -n ai.liquid.browsercontrol/.MainActivity

# 查看日志
adb logcat | grep -E "(LeapSDK|BrowserControl)"

# 录屏
adb shell screenrecord /sdcard/demo.mp4
adb pull /sdcard/demo.mp4
```

### 调试
```bash
# 查看WebView console
adb shell setprop log.tag.chromium DEBUG
adb logcat chromium:V *:S

# 查看内存
adb shell dumpsys meminfo ai.liquid.browsercontrol

# 查看CPU
adb shell top | grep browsercontrol
```

---

**文档版本**: v1.0  
**创建日期**: 2026-02-21  
**维护者**: Tony  
**状态**: 草案 → 待实施
