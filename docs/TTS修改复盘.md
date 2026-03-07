# TTS 修改复盘总结

## 问题背景

用户在运行 `decoupled_agent.py` 时发现两个问题：
1. TTS 播放最后一个字时会爆音
2. LLM 输出是一段一段的，不连续

## 修改历程

### 第一阶段：解决爆音问题

**问题**：TTS 音频播放结束时，最后一个字会突然截断，产生爆音。

**解决方案**：在 TTS 服务返回音频前，添加末尾淡出处理。

**修改文件**：
- `src/services/tts_service.py`：添加 `_apply_fade_out` 函数
- `src/services/tts/stream_tts.py`：在流式输出前应用淡出

**代码示例**：
```python
def _apply_fade_out(audio_data: bytes, fade_samples: int = 480) -> bytes:
    """末尾淡出处理，防止爆音（约20ms@24kHz）"""
    if not NUMPY_AVAILABLE or len(audio_data) < fade_samples * 2:
        return audio_data
    try:
        data = np.frombuffer(audio_data, dtype=np.int16)
        fade_len = min(fade_samples, len(data))
        fade_curve = np.linspace(1.0, 0.0, fade_len)
        data[-fade_len:] = (data[-fade_len:] * fade_curve).astype(np.int16)
        return data.tobytes()
    except Exception:
        return audio_data
```

---

### 第二阶段：解决分段输出问题

**问题**：LLM 输出是一段一段的，需要等待 TTS 合成完才能继续接收下一个 chunk。

**尝试方案 A**：使用 `StreamTTSService` 实现真正的流式 TTS
- 效果不理想，因为 TTS 服务本身也是等待整个文本段合成完才输出

**最终方案 B**：双队列架构

**架构设计**：
```
LLM输出 → 文本队列 → TTS消费者 → 音频队列 → 播放器
   ↓              ↓
  并行          并行
```

**修改文件**：`src/core/agent.py`

**核心改动**：

1. **AudioPlayer**：添加 `wait_finish()` 方法，等待音频播放完成

2. **TTSTask**：重写为双队列架构
   - `_text_queue`：存储 LLM 输出的文本
   - `_audio_queue`：存储 TTS 合成的音频
   - `_tts_consumer`：后台任务，从文本队列取文本合成音频
   - `_audio_player_task`：后台任务，从音频队列取音频播放

3. **文本累积策略**：添加 `_text_buffer`，只有遇到标点才触发合成
   ```python
   PUNCTUATION_SET = frozenset("。！？，、；：！？")
   
   async def add_text(self, text: str):
       """添加文本到队列，遇到标点时触发合成"""
       self._text_buffer = getattr(self, "_text_buffer", "") + text
       
       if self._text_buffer and self._text_buffer[-1] in self.PUNCTUATION_SET:
           text_to_synthesize = self._text_buffer
           self._text_buffer = ""
           await self._text_queue.put(text_to_synthesize)
   ```

4. **修复 _finished 逻辑**：收到 None 后检查队列是否为空，不为空则继续处理

5. **添加调试日志**：打印每次 synthesize 调用的次数、文本长度、音频大小

---

### Debug 过程中发现的问题

1. **每个 LLM chunk 都触发 synthesize**
   - 原因：没有文本累积策略
   - 解决：添加标点触发机制

2. **只播放第一段音频**
   - 原因：`_audio_player_task` 收到第一个 None 就退出
   - 解决：收到 None 后检查队列是否为空

3. **LLM 输出被阻塞**
   - 原因：`await tts_task.add_text(text)` 会等待完成
   - 解决：改用 `asyncio.create_task(tts_task.add_text(text))`

---

## 最终架构

```
用户输入
    ↓
ReQuery → 工具判断 → Message构建
    ↓
LLM流式输出
    ↓
┌─────────────────────────────────────┐
│  add_text()                         │
│  - 累积文本到 _text_buffer          │
│  - 遇到标点 → 放入文本队列           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  _tts_consumer (后台任务)           │
│  - 从文本队列取文本                  │
│  - 调用 synthesize()                 │
│  - 放入音频队列                      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  _audio_player_task (后台任务)       │
│  - 从音频队列取音频                  │
│  - 放入 AudioPlayer                 │
└─────────────────────────────────────┘
    ↓
AudioPlayer 播放音频
    ↓
finish() 等待播放完成
```

---

## 待优化项

1. **淡出参数可调**：目前固定 20ms，可根据实际情况调整
2. **首段加速**：第一段文本可以更短，减少等待时间
3. **WebSocket 复用**：目前每次 synthesize 都创建新连接，可考虑复用

---

## 总结

本次修改实现了 LLM 输出和 TTS 合成的真正并行，通过双队列架构和文本累积策略，解决了：
1. 爆音问题（淡出处理）
2. 分段输出问题（并行处理 + 标点触发）

核心思路是将复杂的同步流程拆解为独立的异步任务，通过队列解耦，实现真正的流式处理。
