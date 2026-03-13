# TTS 文本切分与服务流程详解

## 一、整体架构

```
LLM 流式输出
    ↓
agent.py 缓冲区 (add_text)
    ↓ _text_queue
StreamTTS / base.py 二次切分
    ↓ _audio_queue
AudioPlayer 播放
```

---

## 二、agent.py 缓冲区逻辑

### 2.1 核心参数

```python
PUNCTUATION_END = frozenset("。！？")     # 句末标点 - 立即触发
PUNCTUATION_PAUSE = frozenset("，、；：")  # 句中标点 - 累积更多
MIN_CHUNK_LENGTH = 8                      # 最小累积长度
MAX_CHUNK_LENGTH = 60                     # 最大累积长度强制触发
```

### 2.2 触发流程

```
add_text(text):
│
├─ 1. 累积文本到缓冲区
│   └─ _text_buffer += text
│
├─ 2. 策略1：遇句末标点立即触发
│   └─ 条件：_text_buffer[-1] in PUNCTUATION_END
│       └─ 结果：清空缓冲区，放入 _text_queue，返回
│
├─ 3. 策略2：句中标点+累积≥8字触发
│   └─ 条件：buffer_len ≥ 8 AND _text_buffer[-1] in PUNCTUATION_PAUSE
│       └─ 结果：清空缓冲区，放入 _text_queue，返回
│
└─ 4. 策略3：累积≥60字强制触发
    └─ 条件：buffer_len ≥ 60
        └─ 结果：清空缓冲区，放入 _text_queue，返回
```

### 2.3 日志输出示例

```
[TTS] 句末标点触发 | 缓冲区=25字 | 文本='看到花和草时，不要随意踩踏或采摘哦，小草也会疼的！'
[TTS] 句中标点+长度触发 | 缓冲区=35字 | 文本='有些植物可能有刺或会让皮肤痒痒，所以不要随便摸。我们可以安静地欣赏它们'
[TTS] 长度强制触发 | 缓冲区=60字 | 文本='...'
[TTS] finish时flush | 缓冲区=15字 | 文本='你觉得怎么做更好呢？'
```

---

## 三、base.py 二次切分逻辑

### 3.1 核心参数

```python
# 标点符号定义
STRONG_PUNCTUATIONS = ("。", "？", "！", "；", "…")  # 强标点
ALL_PUNCTUATIONS = ("，", ",", "。", "？", "！", "；", "、", "…", "：", ":")

# 切分阈值
MIN_SEGMENT_LENGTH = 8        # 短句合并阈值（<8字继续累积）
FAST_RESPONSE_LENGTH = 15     # 保留兼容性
LONG_SEGMENT_LENGTH = 20     # 长句拆分阈值（≥20字尝试拆分）
```

### 3.2 完整切分流程

```
_get_segment_text():
│
├─ 1. 整句保护（优先）
│   └─ 条件：current_text[-1] in STRONG_PUNCTUATIONS AND len(current_text) ≤ 30
│       └─ 结果：processed_chars += len(current_text)，返回完整句子
│
├─ 2. 长文本保护
│   └─ 条件：processed_chars == 0 AND len(current_text) > 30
│       └─ 结果：processed_chars += len(current_text)，返回整段
│
├─ 3. 查找标点位置
│   ├─ strong_pos: 第一个强标点位置(。！？；…)
│   ├─ comma_pos: 第一个逗号位置(，,)
│   └─ other_pos: 第一个其他标点位置(、：)
│
├─ 4. 标点切分（按优先级）
│   │
│   ├─ 强标点：
│   │   ├─ segment_len ≥ 20 → 调用 _split_long_segment 拆分
│   │   └─ 否则直接返回
│   │
│   ├─ 逗号：
│   │   ├─ segment_len ≥ 8 → 继续
│   │   │   ├─ segment_len ≥ 20 → 拆分
│   │   │   └─ 否则直接返回
│   │   └─ segment_len < 8 → 继续累积（返回None）
│   │
│   └─ 其他标点：
│       ├─ segment_len ≥ 8 → 继续
│       │   ├─ segment_len ≥ 20 → 拆分
│       │   └─ 否则直接返回
│       └─ segment_len < 8 → 继续累积
│
├─ 5. 无标点处理
│   └─ len(current_text) ≥ 20 → _split_long_segment()
│   └─ 否则返回 None（继续累积）
│
└─ 6. _split_long_segment(text)
    │
    ├─ 找候选拆分位置：
    │   ├─ 最后一个逗号位置
    │   ├─ 最后一个顿号位置
    │   ├─ 最后一个空格位置
    │   └─ 最后一个句末标点位置
    │
    ├─ 选择最接近中间的位置
    │
    └─ 返回前半部分，剩余放回 tts_text_buff
```

### 3.3 切分决策表

| 场景 | 条件 | 处理 |
|------|------|------|
| 整句保护 | ≤30字 + 句末标点 | 直接返回，不切分 |
| 长文本保护 | > 30字（来自上游）| 直接返回，不切分 |
| 继续累积 | < 8字 | 返回 None |
| 正常切分 | 8-20字 + 标点 | 按标点位置切分 |
| 长句拆分 | ≥ 20字 | 调用 _split_long_segment |

---

## 四、TTS 转换服务流程

### 4.1 StreamTTS 核心逻辑

```
StreamTTS.process_llm_stream(llm_stream):
│
├─ 1. 初始化
│   ├─ provider.reset()     # 重置状态
│   └─ provider.start()     # 启动处理线程
│
├─ 2. 并发执行（asyncio.gather）
│   │
│   ├─ feed_llm_stream(): 消费LLM流
│   │   │
│   │   ├─ async for text_chunk in llm_stream:
│   │   │   └─ provider.put_text(text_chunk)
│   │   │
│   │   └─ finally:
│   │       └─ provider.finish_text()  # 发送结束信号
│   │       └─ feed_done.set()
│   │
│   └─ get_audio_stream(): 获取音频
│       │
│       └─ while True:
│           ├─ message = provider.get_audio(timeout=30)
│           ├─ if message is None:
│           │   └─ if feed_done: break
│           ├─ if content_type == END: break
│           ├─ if content_type == ERROR: print error
│           └─ if content_type == AUDIO:
│               └─ yield (audio_data, text)
│
└─ 3. 清理
    ├─ feed_task.cancel()
    └─ provider.stop()
```

### 4.2 provider 内部处理线程

```
_text_processing_thread():
│
├─ 1. 创建事件循环
│   └─ _loop = asyncio.new_event_loop()
│
├─ 2. 主循环
│   └─ while not stop_event:
│       │
│       ├─ message = tts_text_queue.get(timeout=1.0)
│       │
│       ├─ if content_type == END:
│       │   ├─ _process_remaining_text()
│       │   └─ put(END)，break
│       │
│       └─ if content_type == TEXT:
│           ├─ _filter_text(text)
│           ├─ tts_text_buff.append(filtered_text)
│           ├─ segment = _get_segment_text()
│           │   └─ 如返回有效segment，调用 _process_tts_segment(segment)
│           └─ _process_tts_segment(text):
│               ├─ audio_generator = _stream_tts_impl(text)
│               ├─ async for audio_chunk in audio_generator:
│               │   └─ tts_audio_queue.put(AUDIO, audio_chunk, text)
│               └─ except: tts_audio_queue.put(ERROR, error)
│
└─ 3. 关闭
    └─ _loop.close()
```

---

## 五、播放逻辑流程

### 5.1 双队列架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   LLM 流输出    │ ──▶ │   _text_queue   │ ──▶ │  TTS 合成服务   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  _audio_queue   │
                                               └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  AudioPlayer    │
                                               └─────────────────┘
```

### 5.2 TTS 消费者 (_tts_consumer)

```
_tts_consumer():
│
├─ while True:
│   │
│   ├─ 1. 处理预加载结果
│   │   └─ pending_results 队列中的结果放入 _audio_queue
│   │
│   ├─ 2. 获取文本段
│   │   └─ text_segment = await _text_queue.get()
│   │
│   ├─ 3. 触发合成
│   │   └─ result = await tts_service.synthesize(text_segment)
│   │
│   ├─ 4. 放入音频队列
│   │   └─ if result.success:
│   │       └─ await _audio_queue.put(result.audio_data)
│   │
│   └─ 5. 退出条件
│       └─ if text_segment is None and _text_queue.empty():
│           └─ break
│
└─ 循环结束
    └─ await _audio_queue.put(None)  # 发送结束信号
```

### 5.3 音频播放任务 (_audio_player_task)

```
_audio_player_task():
│
├─ while True:
│   │
│   ├─ 获取音频
│   │   └─ audio_data = await _audio_queue.get()
│   │
│   ├─ 结束信号
│   │   └─ if audio_data is None:
│   │       ├─ await asyncio.sleep(0.3)  # 等待确认
│   │       └─ if _audio_queue.empty(): break
│   │
│   └─ 播放音频
│       └─ await player.play(audio_data)
│
└─ 退出
    └─ await audio_queue.put(None)  # 通知播放结束
```

### 5.4 finish() 流程

```
finish():
│
├─ 1. 刷新剩余文本
│   └─ if _text_buffer:
│       └─ await _text_queue.put(_text_buffer)
│       └─ _text_buffer = ""
│
├─ 2. 发送结束信号
│   └─ await _text_queue.put(None)
│
├─ 3. 设置完成标志
│   └─ _finished = True
│
└─ 4. 等待 TTS 任务
    └─ if _tts_task: await _tts_task
```

---

## 六、日志格式规范

### 6.1 agent.py 日志

```
[TTS] 句末标点触发 | 缓冲区=25字 | 文本='完整句子内容'
[TTS] 句中标点+长度触发 | 缓冲区=35字 | 文本='...'
[TTS] 长度强制触发 | 缓冲区=60字 | 文本='...'
[TTS] finish时flush | 缓冲区=15字 | 文本='...'

=== [TTS Chunk #1] 合成中 (长度=25) ===
    文本内容: 完整句子内容
    字符数: 25
[TTS Chunk #1] >> 合成成功 75KB
```

### 6.2 AudioPlayer 日志

```
=== [AudioPlayer] 播放循环启动 ===
=== [AudioTask] 启动 ===
[AudioTask] >> 收到音频 75KB
[AudioPlayer #1] >> 播放 75KB
[AudioPlayer #1] >> 播放完成
```

---

## 七、关键设计要点

### 7.1 文本累积策略

1. **优先句子完整**：遇句末标点立即触发
2. **合并短句**：句中标点+≥8字触发
3. **防止截断**：MAX_CHUNK_LENGTH=60

### 7.2 双层保护机制

1. **整句保护**：≤30字+句末标点，直接返回
2. **长文本保护**：>30字，直接返回

### 7.3 队列同步机制

1. **None 信号**：作为队列结束标志
2. **_finished 标志**：延迟设置，确保所有文本入队
3. **等待确认**：收到 None 后等待 0.3s 确认队列清空

### 7.4 并发模型

1. **TTS 合成与播放并行**：_tts_consumer 和 _audio_player_task 并发
2. **串行合成**：当前实现为串行合成，保证顺序
3. **并行思考**：后续可考虑并行合成+序号排序

---

## 八、待优化问题

### 8.1 首段太长导致回复速度慢

- **现象**：第一段累积到 60 字，需等待整段 TTS 合成完
- **方案A**：分段并行合成（第一段累积到15字就触发）
- **方案B**：快速首段（前N字先合成让用户先听到）

### 8.2 并行合成顺序问题

- **现象**：如开启并行合成，不同长度块完成时间不同
- **解决**：需要序号标记 + 按序号排序播放

### 8.3 base.py 代码优化

- 暂无死代码，已清理完成
