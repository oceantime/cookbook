# Skill: 模型检查点管理

**类别**: MLOps / 模型管理  
**适用场景**: 管理大型模型检查点的存储、命名和备份  
**创建时间**: 2026-02-22

---

## 命名约定

```
{model_name}-{task}-{timestamp}
LFM2-350M-browsergym-20260220-182152
```

## 版本控制策略

- 检查点名称中添加时间戳
- WandB 运行中添加标签
- 配置中记录 Git 提交哈希

## 存储体积管理（检查点约 1.4GB/个）

### Modal 存储卷（云端）

```bash
# 列出所有检查点
modal volume ls browser-control-fine-tune-with-grpo

# 选择性下载（仅需要的检查点）
modal volume get volume-name remote-path local-path
```

### Docker Volume 检查点提取（本地 Docker 训练）

训练检查点保存在 Docker named volume 中，需用轻量容器桥接到宿主机：

```bash
# 列出 volume 中所有检查点
docker run --rm -v browser-control-checkpoints:/ckpt alpine ls /ckpt/

# 复制指定检查点到宿主机（21G 约需 2-3 分钟）
docker run --rm \
  -v browser-control-checkpoints:/ckpt \
  -v /path/to/local/checkpoints:/out \
  alpine sh -c "cp -r /ckpt/<checkpoint-name> /out/ && echo '复制完成'"
```

**关键点**：
- `alpine` 镜像轻量（< 10MB），无需额外安装工具，`cp` 即可
- 同时 `-v` 挂载 volume 和宿主机目录，alpine 容器内可跨界 `cp`
- 复制完成后验证：`ls -lh /path/to/local/checkpoints/<checkpoint-name>/`
- 预期文件：`model.safetensors`, `config.json`, `tokenizer.json`, `checkpoint-N/` 等

**DGX Spark 实测**（run31，21.2G）：`cp -r` 约 2-3 分钟，无需 `--archive` 参数。

### 本地存储管理

```bash
# 共享缓存的符号链接
ln -s /shared/hf-cache ~/.cache/huggingface

# 压缩归档
tar -czf checkpoint.tar.gz checkpoint_dir/
```

### 量化减小体积

| 方法 | 体积减少 |
|------|---------|
| FP16 → Q8_0 | 减小 2.8 倍 |
| FP16 → Q4_K_M | 减小 3.1 倍 |

## 备份策略

1. **主要**: Modal 存储卷（云端，持久）
2. **次要**: 本地磁盘（开发用）
3. **可选**: HuggingFace Hub（团队共享）

## WandB 监控

```python
import wandb

wandb.log({
    "reward": reward,
    "loss": loss,
    "episode": episode,
})
# 查看: https://wandb.ai/project-name/run-id
```
