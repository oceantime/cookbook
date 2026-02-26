# Skill: ARM64 + CUDA 13 开发

**类别**: 基础设施 / 硬件  
**适用场景**: 在 ARM64 服务器（DGX Spark/GB200）上进行 GPU 开发  
**创建时间**: 2026-02-22

---

## 关键发现

**PyTorch CUDA 13.0 是首个支持 ARM64 的 CUDA 版本**（CUDA 12.x 不支持 ARM64）

## pyproject.toml 配置

```toml
[project]
dependencies = ["torch>=2.10.0"]

[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch-cu130" }
torchvision = { index = "pytorch-cu130" }
```

## 环境验证

```bash
# 检查架构
uname -m  # 应显示: aarch64

# 检查 CUDA 版本
nvidia-smi  # 应显示: CUDA Version: 13.0

# 验证 PyTorch CUDA
python -c "import torch; print(torch.__version__)"   # 2.10.0+cu130
python -c "import torch; print(torch.cuda.is_available())"  # True
```

## CUDA 版本平台支持矩阵

| CUDA 版本 | x86_64 | ARM64 | 备注 |
|-----------|--------|-------|------|
| 11.8 | ✅ | ❌ | 旧版 |
| 12.1 | ✅ | ❌ | 常见 |
| 12.4 | ✅ | ❌ | LTS |
| 12.6 | ✅ | ❌ | 最新 12.x |
| **13.0** | ✅ | **✅** | **首个 ARM64 支持** |

## 适用硬件

- NVIDIA DGX Spark
- GB10、GB20、GB200
- 其他基于 ARM64 的 NVIDIA 服务器

## 为什么重要

- 可在 ARM64 服务器上直接本地开发
- 无需等待模型上传到云端
- 比 Modal 云端转换快 100-200 倍

## 参考

- [DGX Spark 论坛](https://forums.developer.nvidia.cn/t/dgx-spark-vllm-cuda13/28377)
- PyTorch ARM64 Wheel: https://download.pytorch.org/whl/cu130
