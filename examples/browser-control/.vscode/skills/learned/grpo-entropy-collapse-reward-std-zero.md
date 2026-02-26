# Skill: GRPO entropy 崩溃与 reward_std=0 死锁

**类别**: 机器学习 / GRPO 调试  
**适用场景**: GRPO 训练时 entropy 骤降至接近 0，loss/grad_norm 归零  
**创建时间**: 2026-02-26  
**验证环境**: LFM2-350M + TRL GRPOTrainer + BrowserGym MiniWoB click-test，DGX Spark B10

---

## 症状

```
entropy: 0.007   # 正常应为 2.0+
loss: 0.0
grad_norm: 0.0
reward: 1.0
reward_std: 0.0
frac_reward_zero_std: 1.0
```

模型对每个 token 以近乎 100% 概率输出同一动作，陷入死锁。

---

## 根因：reward_std=0 → advantage=0 → 无梯度

GRPO 核心公式：

```
advantage_i = (reward_i - mean(rewards)) / (std(rewards) + eps)
```

当所有 rollout 的 reward **完全相同**（全为 1.0 或全为 0.0）时：

- `reward_std = 0`
- `advantage = 0`（分子为 0）
- `loss = 0`，`grad_norm = 0`
- 模型权重不再更新，永久锁死

---

## 崩溃时间线（run30，LR=5e-6，单一任务 click-test）

| Step | 事件 | entropy | loss | grad_norm |
|------|------|---------|------|-----------|
| 1-12 | warmup，全部 reward=0，reward_std=0 | 2.3~2.8 | 0.0 | 0.0 |
| 13 | 首次 reward=0.75，reward_std=0.5 | 1.53 | -0.008 | 0.53 |
| 17 | reward=0.5，开始学习 | 0.58 | -0.121 | **6.4** |
| 20 | **灾难性更新**，grad_norm=10.7 | **0.56** | -0.246 | **10.7** |
| 21 | reward=1.0，**reward_std=0，死锁开始** | **0.04** | 0.0 | 0.0 |
| 21~100 | 永久死锁 | ~0.006 | 0.0 | 0.0 |

---

## 触发条件

只要同时满足以下条件，任何 GRPO 训练都会死锁：

1. **训练集任务种类单一**（如只有 click-test 一种任务）
2. **模型学会该任务**（所有 rollout reward=1.0）
3. **num_generations 个 rollout reward 全部相同**

---

## 修复方案

### 方案一：降低 learning_rate（治标，推迟崩溃）

```yaml
# 从 5e-6 降至 1e-6
learning_rate: 1.0e-6
```

**效果（run31 对比 run30）**：

| Step | run30 entropy | run31 entropy |
|------|--------------|--------------|
| 20 | **0.56**（崩溃） | **2.50**（健康） |
| 36 | 0.007 | 2.16 |
| 100 | 0.006 | 0.13~0.46 |

- run31 最终 entropy=0.13~0.46，比 run30 的 0.006 高约 25 倍
- `train_loss=-0.007`（非零，有实际学习）
- 但最终仍会因单一任务死锁（entropy 仍在下降）

### 方案二：增加任务多样性（治本）

在 BrowserGym 中混合多种 MiniWoB 任务：

```python
# 在 rollout_func 中随机选择任务
TASKS = [
    "click-test",
    "click-button",
    "type-text",
    "navigate-tree",
    "focus-text",
]
task = random.choice(TASKS)
```

只要不同 rollout 的任务不同，reward 就不会完全一致，`reward_std > 0`，梯度不归零。

### 方案三：添加 entropy 正则化

```python
# GRPOConfig 中设置 entropy 惩罚系数
entropy_regularization=0.01  # 鼓励保持 entropy
```

防止模型过快收敛到确定性策略。

---

## 快速诊断清单

观察到以下任意一项，立即检查 entropy 和 reward_std：

- [ ] `frac_reward_zero_std: 1.0`（所有 rollout reward 相同）
- [ ] `completions/mean_length` 完全固定（如一直是 5.0）
- [ ] `step_time` 突然从 ~140s 降至 ~0.08s（无 rollout，纯空循环）
- [ ] `entropy < 0.1`

---

## 正常训练基准（LFM2-350M，click-test，LR=1e-6）

| Step 范围 | entropy | 说明 |
|-----------|---------|------|
| 1-10（warmup） | 2.3~2.8 | 正常，全为 reward=0 |
| 11-20（首次学习） | 1.5~2.5 | 有梯度，reward_std>0 |
| 21+（学会后） | 0.1~0.5 | 缓慢下降（LR=1e-6），或死锁（LR=5e-6） |

---

## 相关技能

- `grpo-reinforcement-learning.md`：GRPO 基本原理
- `grpo-reward-func-from-rollout.md`：reward_func 接线
- `browsergym-environment.md`：BrowserGym HTTP REST 接口
