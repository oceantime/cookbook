# Skill: Modal 无服务器 GPU 基础设施

**类别**: 云计算 / MLOps  
**适用场景**: 无需管理服务器的云端 GPU 执行  
**创建时间**: 2026-02-22

---

## 核心概念

### 1. 镜像（容器定义）

```python
import modal

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "build-essential")
    .pip_install("transformers", "torch", "trl")
)
```

### 2. 函数（GPU 任务）

```python
@app.function(
    image=image,
    gpu="A100",
    timeout=3600,
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("wandb-secret")]
)
def train_model():
    pass
```

### 3. 存储卷（持久化存储）

```python
volume = modal.Volume.from_name(
    "browser-control-fine-tune-with-grpo",
    create_if_missing=True
)

@app.function(volumes={"/checkpoints": volume})
def save_checkpoint():
    torch.save(model.state_dict(), "/checkpoints/model.pt")
    volume.commit()  # 必须调用！
```

### 4. 密钥（环境变量）

```python
secrets=[modal.Secret.from_name("wandb-secret")]

# 在函数中访问
import os
wandb_key = os.environ["WANDB_API_KEY"]
```

## 本地 + 远程开发模式

```python
app = modal.App("browser-control")

@app.function(gpu="A100")
def train():
    pass

@app.local_entrypoint()
def main():
    train.remote()  # 在 Modal GPU 上执行
```

## Volume 常用命令

```bash
# 列出检查点
modal volume ls browser-control-fine-tune-with-grpo

# 下载指定文件
modal volume get volume-name remote-path local-path
```

## Modal Volume Race Condition 处理

```python
# 使用 batch_upload 避免竞争条件
with volume.batch_upload() as batch:
    batch.put_file("file1.txt", "/remote/path1")
    batch.put_file("file2.txt", "/remote/path2")
# 退出时自动 commit
```

## 最佳实践

- 使用存储卷存放大文件（模型、数据）
- 写入后必须调用 `volume.commit()`
- 缓存镜像层以加快构建速度
- 设置合理的 `timeout`（默认 300 秒可能不够）
- 在控制台监控成本: https://modal.com/oceantime

## 参考

- Modal 文档: https://modal.com/docs
- 定价: 按秒计费 GPU 使用
