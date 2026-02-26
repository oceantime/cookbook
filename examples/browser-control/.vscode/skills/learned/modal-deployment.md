# Modal 云端构建配置

## 背景
Modal 是无服务器 GPU 计算平台，本项目使用 Modal 运行 GRPO 微调和 GGUF 转换。

## 基础设施组件

### Docker 镜像
```python
# modal_infra.py
modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .uv_pip_install(
        "trl[vllm]",
        "git+https://github.com/meta-pytorch/OpenEnv.git@bf5e968",
        "openenv_core==0.1.1",
        "liger-kernel",
        "wandb",
        "peft>=0.13.0",
    )
```

### Volumes
```python
hf_models_volume = modal.Volume.from_name("hf-model-cache", create_if_missing=True)
checkpoints_volume = modal.Volume.from_name("browser-control-fine-tune-with-grpo", create_if_missing=True)
```

### Secrets
```bash
# 创建 WandB secret
modal secret create wandb-secret WANDB_API_KEY=<your-key>
```

## 运行命令

```bash
# 微调
uv run modal run -m src.browser_control.fine_tune --config-file-name lfm2_350m.yaml

# GGUF 转换
uv run modal run -m src.browser_control.convert_to_gguf_modal

# 通过 Makefile
make fine-tune config=lfm2_350m.yaml
```

## GPU 配置
```python
@app.function(
    gpu="A100-80GB",
    timeout=3600,
    volumes={"/hf_model_cache": hf_models_volume},
)
```

## 注意事项
- Modal 函数每次调用都从干净状态启动，依赖缓存在 Volume 中
- `wandb_enabled: false` 可在调试时关闭 WandB 追踪
- Modal 费用按 GPU 秒计费，训练完成后资源自动释放
- 使用 `modal app list` 查看运行中的任务
