FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/hf_cache

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip3 install uv

WORKDIR /workspace

# Copy OpenEnv (must be cloned first: git clone https://github.com/meta-pytorch/OpenEnv.git)
COPY OpenEnv/ /workspace/OpenEnv/

# Copy project files
COPY ../../pyproject.toml ../../uv.lock ./
COPY ../../src/ ./src/
COPY ../../configs/ ./configs/

# Install dependencies
RUN uv sync

ENV PYTHONPATH=/workspace

CMD ["python3", "-m", "src.browser_control.fine_tune_local", "--config-file-name", "lfm2_350m_local_lora.yaml"]
