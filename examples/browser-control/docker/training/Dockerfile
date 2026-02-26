# syntax=docker/dockerfile:1
# GPU训练容器镜像 (第12次构建)
# 策略：从已有镜像复用 Python 3.12 + 所有 pip 包，只新增 triton 3.6.0
# 基于CUDA 12.8 + Ubuntu 22.04
# vllm 0.12.0 需要 torch==2.9.0，torch 2.9.0 aarch64 CUDA wheel 只有 cu128 版本
# 宿主机驱动 580（CUDA 13.0）向下兼容，容器内 CUDA 12.8 完全支持 GB10

# 第一阶段：从已有镜像中提取所有已安装的包（复用缓存，跳过漫长的 PPA/pip 下载）
FROM docker-training:latest AS base

# 第二阶段：最终镜像，基于相同 CUDA 基础镜像
FROM docker-training:latest

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHON_VERSION=3.12 \
    HF_HOME=/hf_model_cache \
    UV_SYSTEM_PYTHON=1 \
    PYTHONUNBUFFERED=1

# 换用清华 Ubuntu 镜像源（加速 apt 下载）
RUN sed -i 's|http://ports.ubuntu.com|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list 2>/dev/null || true && \
    sed -i 's|http://security.ubuntu.com|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list 2>/dev/null || true

# 配置 pip 使用清华 PyPI 镜像
RUN python3.12 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    python3.12 -m pip config set global.extra-index-url https://pypi.org/simple

# 升级 triton 到 3.6.0，以支持 sm_121a (GB10 Blackwell CC 12.1)
# 旧镜像中 vllm 0.12.0 安装的 triton 3.5.0 生成 PTX 8.5，不支持 sm_121a
# triton 3.6.0 修复了此问题（PyPI 有 cp312 aarch64 wheel，清华镜像有同步）
RUN --mount=type=cache,target=/root/.cache/pip \
    python3.12 -m pip install "triton==3.6.0"

# 验证版本
RUN python3.12 -c "import importlib.metadata; print('vllm:', importlib.metadata.version('vllm')); print('torch:', importlib.metadata.version('torch')); print('triton:', importlib.metadata.version('triton')); print('OK')"

# 将 nvidia pip 包的库路径加入 LD_LIBRARY_PATH（vllm 依赖安装的 nvidia-* 包）
ENV LD_LIBRARY_PATH=/usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib:/usr/local/lib/python3.12/dist-packages/nvidia/cublas/lib:/usr/local/cuda/lib64:/usr/local/cuda-12.8/lib64:/usr/local/lib

# 复制并安装本地 OpenEnv
COPY OpenEnv /tmp/OpenEnv
RUN --mount=type=cache,target=/root/.cache/pip \
    cd /tmp/OpenEnv && \
    python3.12 -m pip install . && \
    cd / && rm -rf /tmp/OpenEnv

# 工作目录
WORKDIR /workspace

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import torch; assert torch.cuda.is_available()" || exit 1

# 默认命令
CMD ["bash"]
