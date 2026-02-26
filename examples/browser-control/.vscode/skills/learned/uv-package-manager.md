# Skill: uv 包管理器

**类别**: Python 开发工具  
**适用场景**: 替代 pip/conda 的快速 Python 包管理  
**创建时间**: 2026-02-22

---

## 核心优势

- 比 pip 快 **10-100 倍**
- 确定性依赖解析（锁文件）
- 兼容 pip 命令
- 内置虚拟环境管理

## 常用命令

```bash
# 初始化项目
uv init

# 从 pyproject.toml 安装依赖
uv sync

# 添加/移除包
uv add package-name
uv remove package-name

# 在虚拟环境中运行命令
uv run python script.py
uv run modal run app.py

# pip 兼容命令
uv pip install httpx[socks]
uv pip list
```

## 自定义包索引（关键：PyTorch ARM64）

```toml
# pyproject.toml
[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch-cu130" }
torchvision = { index = "pytorch-cu130" }
```

## 锁文件

`uv.lock` 锁定所有依赖的精确版本，保证可重现性：

```bash
# 锁文件存在时，sync 使用锁文件版本
uv sync

# 更新锁文件
uv lock --upgrade
```

## 参考

- 文档: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
