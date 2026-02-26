# MiniWoB++ JS API 交互：episode 控制与 reward 捕获

> **适用范围**: 本项目（BrowserControlDemo + browser-control 训练验证）  
> **标签**: miniwob, javascript, webview, reward, episode, timer

---

## 核心 API 速查

| API | 说明 | 陷阱 |
|-----|------|------|
| `core.startEpisodeReal(seed)` | 启动 episode，seed=null 随机 | 必须在拦截器安装后调用 |
| `core.endEpisode(reward)` | 结束 episode（1=成功，-1=失败）| 调用后页面重置，getReward() 失效 |
| `core.getReward()` | 读取当前 reward | **episode 结束重置后返回 null**，勿依赖 |
| `core.EPISODE_MAX_TIME` | 默认 10000ms | 推理期间会超时，需提前调大 |
| `core.timer_.timeoutId_` | 内部 setTimeout ID | 用于手动取消+重设计时 |
| `core.timer_.pauseTimer()` | ❌ **不存在** | 用 clearTimeout 替代 |

---

## 问题1：episode 结束后 `getReward()` 返回 null

**原因**：`core.endEpisode()` 触发页面 DOM 重置，`core` 对象内部状态清空。

**解决**：在 `startEpisodeReal()` 前 monkey-patch `endEpisode`，持久化 reward 到 `window` 变量：

```javascript
window._miniWobEpisodeDone = false;
window._lastMiniWobReward = undefined;

if (!core._endEpisodePatched) {           // 幂等保护，避免多次叠加
    var _orig = core.endEpisode.bind(core);
    core.endEpisode = function(r) {
        window._lastMiniWobReward = r;
        window._miniWobEpisodeDone = true;
        _orig(r);
    };
    core._endEpisodePatched = true;
}
```

**读取 reward**（页面重置后仍有效）：

```javascript
if (window._miniWobEpisodeDone === true) {
    return String(window._lastMiniWobReward);  // "1", "0", "-1"
}
return 'ongoing';
```

---

## 问题2：10s 默认计时器在推理期间超时

**原因**：LFM2-350M 单步推理约 8s，MiniWoB 默认 `EPISODE_MAX_TIME=10000ms`。

**解决**：`startEpisodeReal()` 后立即 clearTimeout + 重设更长的计时器：

```javascript
core.EPISODE_MAX_TIME = 60000;
core.startEpisodeReal(null);

if (core.timer_ && core.timer_.timeoutId_) {
    clearTimeout(core.timer_.timeoutId_);
    core.timer_.timeoutId_ = setTimeout(function() {
        core.endEpisode(-1);
    }, 60000);
}
```

---

## 完整 startEpisode 函数

```javascript
(function() {
    try {
        if (typeof core === 'undefined') return 'no-core';

        window._miniWobEpisodeDone = false;
        window._lastMiniWobReward = undefined;

        if (!core._endEpisodePatched) {
            var _orig = core.endEpisode.bind(core);
            core.endEpisode = function(r) {
                window._lastMiniWobReward = r;
                window._miniWobEpisodeDone = true;
                _orig(r);
            };
            core._endEpisodePatched = true;
        }

        core.EPISODE_MAX_TIME = 60000;
        core.startEpisodeReal(null);

        if (core.timer_ && core.timer_.timeoutId_) {
            clearTimeout(core.timer_.timeoutId_);
            core.timer_.timeoutId_ = setTimeout(function() {
                core.endEpisode(-1);
            }, 60000);
            return 'started+timer_extended_60s+interceptor_ok';
        }
        return 'started+interceptor_ok';
    } catch(e) { return 'error:' + e.message; }
})()
```

---

## 问题3：WebView viewport 注入重复触发

**原因**：`onPageFinished` 在 MiniWoB 上会触发 2-3 次（主页面 + iframe）。

**解决**：`dataset.vpSet` 标志保证只注入一次：

```javascript
(function() {
    if (document.documentElement.dataset.vpSet) return;
    document.documentElement.dataset.vpSet = '1';
    var meta = document.querySelector('meta[name="viewport"]')
             || document.createElement('meta');
    meta.name = 'viewport';
    meta.content = 'width=160';
    document.head.appendChild(meta);
})();
```

---

## Kotlin 集成要点

```kotlin
// 动作执行后轮询 reward，最多 3s
var reward: Double? = null
repeat(10) {
    delay(300)
    val r = withContext(Dispatchers.Main) { getMiniWobReward(webView) }
    if (r != null) { reward = r; return@repeat }
}

// reward > 0 成功 / reward < 0 失败 / null 继续
when {
    reward != null && reward!! > 0 -> { /* 成功, 注入覆盖层 */ }
    reward != null && reward!! < 0 -> { /* 失败, 注入覆盖层 */ }
}
```
