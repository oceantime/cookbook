FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    git \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /workspace

# Copy OpenEnv (must be cloned first: git clone https://github.com/meta-pytorch/OpenEnv.git)
COPY OpenEnv/ /workspace/OpenEnv/

# Install OpenEnv with server extras
RUN cd /workspace/OpenEnv && uv pip install --system -e ".[server,browsergym]"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python3", "-m", "openenv.server", "--port", "8080", "--host", "0.0.0.0"]
