# TTS服务流畅运行分析报告

## 概述

本项目的TTS（文字转语音）服务能够实现流畅的语音输出，无明显停顿，主要得益于以下几个核心设计：

1. **流式处理架构**
2. **双队列缓冲机制**
3. **智能文本分割**
4. **客户端智能播放缓冲**
5. **并发与异步处理**

---

## 一、整体数据流程

```
用户语音/文本输入
        ↓
      [ASR识别]
        ↓
      [LLM流式输出] ─────────────────────────────────┐
        ↓                                              │
   ┌─────────────────────────────────────────────────┐│
   │           StreamTTS (流式TTS管理器)              ││
   │  ┌─────────────┐      ┌─────────────────────┐   ││
   │  │ 文本队列    │ ───→ │ TTS Provider (豆包/ │   ││
   │  │tts_text_   │      │ 通义千问/Edge)       │   ││
   │  │ queue      │      │ - 流式合成           │   ││
   │  └─────────────┘      │ - PCM/MP3输出        │   ││
   │         ↑             └─────────────────────┘   ││
   │         │                      ↓                ││
   │  ┌─────────────┐      ┌─────────────────────┐   ││
   │  │ 文本处理    │ ───→ │ 音频队列            │   ││
   │  │ 线程        │      │ tts_audio_queue     │   ││
   │  │ (标点分割)  │      └─────────────────────┘   ││
   │  └─────────────┘              ↓                ││
   └─────────────────────────────────────────────────┘│
                                   ↓                  │
                         [WebSocket发送音频] ←────────┘
                                   ↓
                         ┌─────────────────────┐
                         │    客户端浏览器      │
                         │  ┌───────────────┐  │
                         │  │ 阻塞队列缓冲   │  │
                         │  │ (≥3包后播放)  │  │
                         │  └───────────────┘  │
                         │         ↓           │
                         │  ┌───────────────┐  │
                         │  │ Opus解码器    │  │
                         │  └───────────────┘  │
                         │         ↓           │
                         │  ┌───────────────┐  │
                         │  │ Web Audio API │  │
                         │  │ 流式播放      │  │
                         │  └───────────────┘  │
                         └─────────────────────┘
```

---

## 二、服务端核心设计

### 2.1 流式TTS架构 (`src/tts/stream_tts.py`)

StreamTTS 是整个TTS系统的核心协调器：

```python
class StreamTTS:
    async def process_llm_stream(self, llm_stream, session_id, on_audio):
        """
        关键设计：
        1. 同时启动两个并发任务：
           - feed_llm_stream(): 消费LLM流，将文本放入队列
           - get_audio_stream(): 从队列获取音频，立即yield
        2. 使用ThreadPoolExecutor处理阻塞的TTS API调用
        """
        # 任务1: 消费LLM流
        async def feed_llm_stream():
            async for text_chunk in llm_stream:
                self.provider.put_text(text_message)  # 放入文本队列
        
        # 任务2: 获取音频流
        async def get_audio_stream():
            while True:
                result = await executor.submit(self.provider.get_audio)
                yield (audio_data, text)
        
        # 并发执行
        feed_task = asyncio.create_task(feed_llm_stream())
        async for audio in get_audio_stream():
            yield audio
```

### 2.2 双队列缓冲机制 (`src/tts/base.py`)

TTSProviderBase 实现了生产者-消费者模式：

```python
class TTSProviderBase:
    def __init__(self):
        # 两个核心队列
        self.tts_text_queue = queue.Queue()   # 文本输入队列
        self.tts_audio_queue = queue.Queue()  # 音频输出队列
        
        # 文本处理相关
        self.tts_text_buff = []           # 文本缓冲区
        self.processed_chars = 0          # 已处理字符位置
        self.is_first_sentence = True     # 是否是第一句
        
        # 标点符号配置
        self.first_sentence_punctuations = ("，", "。", "？", "！", ...)  # 第一句遇到逗号就合成
        self.punctuations = ("。", "？", "！", "；", ...)                 # 后续句子等完整语义
    
    def _text_processing_thread(self):
        """
        独立线程处理文本到音频的转换：
        1. 从文本队列获取消息
        2. 累积文本直到遇到标点
        3. 调用TTS API合成音频
        4. 放入音频队列
        """
        while not self.stop_event.is_set():
            message = self.tts_text_queue.get()
            if message.content_type == ContentType.TEXT:
                self.tts_text_buff.append(filtered_text)
                segment_text = self._get_segment_text()  # 智能分割
                if segment_text:
                    asyncio.run(self._process_tts_segment(segment_text))
```

### 2.3 智能文本分割 (`src/tts/base.py`)

**第一句话快速响应策略**：
- 第一句话遇到逗号（，）就立即开始合成
- 后续句子等待句号、问号、感叹号等完整语义符号

```python
def _get_segment_text(self):
    """
    智能文本分割算法：
    """
    full_text = "".join(self.tts_text_buff)
    current_text = full_text[self.processed_chars:]
    
    # 根据是否是第一句话选择标点集合
    punctuations = (
        self.first_sentence_punctuations  # 包含逗号
        if self.is_first_sentence 
        else self.punctuations            # 只有句号问号等
    )
    
    # 找到第一个标点，立即返回这段文本
    first_punct_pos = find_first_punctuation(current_text, punctuations)
    if first_punct_pos != -1:
        segment = current_text[:first_punct_pos + 1]
        self.is_first_sentence = False  # 第一句处理完后重置
        return segment
```

### 2.4 流式TTS提供者 (`src/tts/providers/qwen_tts.py`)

支持真正的流式合成（边合成边输出）：

```python
class QwenTTSProvider(TTSProviderBase):
    async def _stream_tts_impl(self, text: str):
        """
        真正的流式实现：
        每收到一个音频chunk就立即yield，不等待整句完成
        """
        response = dashscope.MultiModalConversation.call(
            model=self.model,
            text=text,
            stream=True,  # 启用流式
        )
        
        for chunk in response:
            pcm_bytes = base64.b64decode(chunk.output.audio.data)
            yield pcm_bytes  # 立即输出，不等待
```

---

## 三、客户端核心设计

### 3.1 阻塞队列缓冲 (`test/test_page.html`)

客户端使用BlockingQueue实现智能缓冲：

```javascript
class BlockingQueue {
    async dequeue(minCount, timeout, onTimeout) {
        // 等待至少 minCount 个元素，或超时
    }
}

// 音频缓冲策略
const BUFFER_THRESHOLD = 3;    // 至少累积3个音频包
const timeout = 300;           // 超时300ms

async function startAudioBuffering() {
    while (true) {
        // 等待至少3个音频包，或300ms超时
        const packets = await queue.dequeue(3, 300, (count) => {
            log(`缓冲超时，当前${count}包，开始播放`);
        });
        
        if (packets.length) {
            streamingContext.pushAudioBuffer(packets);
        }
    }
}
```

### 3.2 流式解码与播放

```javascript
const streamingContext = {
    queue: [],                    // 已解码PCM队列
    activeQueue: new BlockingQueue(), // 准备播放队列
    
    // Opus解码（独立协程）
    decodeOpusFrames: async function() {
        while (true) {
            for (const frame of pendingFrames) {
                const pcmData = opusDecoder.decode(frame);
                this.activeQueue.enqueue(convertToFloat32(pcmData));
            }
        }
    },
    
    // 音频播放（独立协程）
    startPlaying: async function() {
        while (true) {
            // 等待足够音频数据
            const minSamples = SAMPLE_RATE * 0.1 * 3;
            if (this.queue.length < minSamples) {
                await this.getQueue(minSamples);
            }
            
            // 创建音频缓冲区并播放
            const audioBuffer = audioContext.createBuffer(1, samples.length, 16000);
            audioBuffer.copyToChannel(samples, 0);
            
            // 添加淡入淡出效果
            const gainNode = audioContext.createGain();
            gainNode.gain.linearRampToValueAtTime(1, time + 0.02);  // 20ms淡入
            
            source.connect(gainNode).connect(audioContext.destination);
            source.start();
        }
    }
};
```

### 3.3 淡入淡出效果

避免音频片段之间的爆音：

```javascript
const fadeDuration = 0.02; // 20ms淡入淡出

// 淡入
gainNode.gain.setValueAtTime(0, audioContext.currentTime);
gainNode.gain.linearRampToValueAtTime(1, audioContext.currentTime + fadeDuration);

// 淡出
if (duration > fadeDuration * 2) {
    gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + duration);
}
```

---

## 四、关键时序分析

### 4.1 首音延迟优化

| 阶段 | 优化措施 | 预期延迟 |
|------|----------|----------|
| LLM首Token | 流式输出 | ~0.3-0.5s |
| 文本分割 | 第一句遇逗号即合成 | ~0.1s |
| TTS合成 | 流式API（qwen3-tts-flash） | ~0.2-0.3s |
| 音频传输 | WebSocket二进制 | ~0.05s |
| 客户端缓冲 | 3包或300ms | ~0.1-0.3s |
| **总计** | | **~0.75-1.25s** |

### 4.2 持续播放流畅性

```
时间线示意（假设每段合成0.5s）：

t=0.0s   LLM: "你好，"           TTS: 开始合成"你好，"
t=0.3s   LLM: "我是"            TTS: 合成完成→发送
t=0.5s   LLM: "AI助手。"        TTS: 开始合成"我是AI助手。"
t=0.8s   客户端: 开始播放"你好，"  TTS: 继续合成
t=1.0s   LLM: "今天"            TTS: 合成完成→发送
t=1.3s   客户端: 播放"我是AI助手。" TTS: 开始合成"今天天气..."
...
```

由于TTS合成速度（~0.5s/段）通常快于播放速度（~1s/段），客户端会不断积累缓冲，实现无缝播放。

---

## 五、核心代码位置

| 功能 | 文件路径 | 关键函数/类 |
|------|----------|-------------|
| TTS协调器 | `src/tts/stream_tts.py` | `StreamTTS.process_llm_stream()` |
| 双队列基类 | `src/tts/base.py` | `TTSProviderBase._text_processing_thread()` |
| 文本分割 | `src/tts/base.py` | `TTSProviderBase._get_segment_text()` |
| 流式TTS | `src/tts/providers/qwen_tts.py` | `QwenTTSProvider._stream_tts_impl()` |
| 音频发送 | `core/handle/sendAudioHandle.py` | `sendAudio()`, `sendAudioMessage()` |
| 客户端缓冲 | `test/test_page.html` | `BlockingQueue`, `startAudioBuffering()` |
| 客户端播放 | `test/test_page.html` | `streamingContext.startPlaying()` |

---

## 六、总结

TTS服务流畅运行的核心原因：

1. **流式处理全链路**：LLM流式输出 → TTS流式合成 → WebSocket流式传输 → 客户端流式播放

2. **智能缓冲设计**：
   - 服务端：文本队列 + 音频队列解耦
   - 客户端：3包/300ms缓冲策略平衡延迟与流畅

3. **快速首响策略**：第一句话遇到逗号即开始合成

4. **并发处理**：文本处理线程 + 音频发送协程 + 客户端解码/播放协程并行

5. **音频连续性**：淡入淡出效果消除片段间的爆音
