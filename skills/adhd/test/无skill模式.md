# 工作目录代码讲解

> 对 `F:\code\Agent\story_player` 工作目录的代码讲解。

读完了。这是一个**面向儿童故事机的云端语音交互服务**--设备（ESP32 小智固件）通过 WebSocket 上传语音，服务端完成 VAD 切句 -> 流式 ASR -> LLM -> 流式 TTS，再把合成语音回传。下面按层次讲清楚。

## 一句话定位

FastAPI + DashScope 实现的实时语音对话服务。固件 `hello` 握手后持续上传 16 kHz 裸 Opus，**服务端用 WebRTC VAD 自动切分每轮语音**（不需要固件发 `listen.start`/`listen.stop`），跑完 ASR/LLM/TTS 后回传 24 kHz 裸 Opus，同一连接支持多轮上下文。产品形态是无屏玩具，儿童对着它说话听故事。

## 分层架构（六边形/端口适配器）

`src/story_player/` 是典型的 ports & adapters 结构：

| 层 | 位置 | 职责 |
|---|---|---|
| **API 传输** | `api/websocket.py` | WebSocket 端点、帧分发、错误处理、连接生命周期 |
| **应用编排** | `application/` | 轮次编排（`auto_voice_session`）、单轮服务（`voice_session`）、VAD 分句（`utterance`） |
| **协议** | `protocol/` | 消息解析/构造（`messages`）、会话状态机（`session`） |
| **端口（接口）** | `ports/ai.py` | `SpeechRecognizer` / `LanguageModel` / `SpeechSynthesizer` 三个 Protocol |
| **适配器（实现）** | `adapters/` | DashScope 的 ASR/LLM/TTS 实现 + `factory` 装配 |
| **音频** | `audio/` | Opus 解码（`opus`）、WebRTC VAD（`vad`） |
| **配置** | `config.py` | pydantic-settings，全部参数走 `.env` |

端口层（`ports/ai.py:5-24`）只定义 Protocol，DashScope 是唯一实现。测试用 `tests/fakes.py` 注入假 Provider，**不调真实 API**--这就是适配器隔离的价值。

## 核心数据流：一轮对话的生命周期

```
固件 hello ──► parse_hello 校验 ──► server_hello 回 session_id
固件持续上传 Opus 帧
   │
   ▼  websocket.py:101  decode -> PCM
AutoVoiceSession.handle_pcm  (auto_voice_session.py:52)
   │  喂给 UtteranceSegmenter.feed_pcm
   ▼
VAD 状态机 (utterance.py) 发事件：
   CandidateStarted -> SpeechStarted(含 preroll 预录 PCM) -> SpeechAudio* -> SpeechEnded
   │                    │ (创建 ASR 并 start)              │ (送 ASR)      │ (结束本轮)
   │                    ▼                                                    ▼
   │              asr.send_pcm(pcm)                            创建 _run_turn 后台 task
   │                                                                        │
   ▼                                                                        ▼
SpeechEnded 触发 session.finish_listening() (LISTENING->PROCESSING)
                                                     VoiceTurnService.run_turn (voice_session.py:48)
                                                         │
                                                         ▼ asr.finish() 拿文本
                                                         ▼ 发 stt 消息
                                                         ▼ llm.stream() 流式出 token
                                                         ▼ _take_sentences 按句号/问号切句
                                                         ▼ 每句 stream_tts() 流式出 Opus 包
                                                         ▼ 发 tts.start / 逐包 send_bytes / tts.stop
                                                         ▼ session.finish_speaking 存历史 (SPEAKING->IDLE)
                                                         ▼ start_listening 进下一轮
```

关键点：**ASR/LLM/TTS 全程流式，边生成边下发**。LLM 出 token 就攒句，遇到 `。！？；` 切出一句立刻送 TTS，不等整段 LLM 跑完。这是压低"首字响应延迟"的核心手段。

## 几个值得注意的设计

**1. VAD 分句器（`utterance.py`）是状态机**，三态 `idle -> candidate -> active`：
- `idle`：滑窗（默认 5 帧）里命中语音帧数达阈值（默认 3）才进 `candidate`，防噪点误触发；
- `candidate`：攒够 `min_speech_ms`（300ms）确认是真说话 -> `active` 并发出 `SpeechStarted`（带 preroll 预录的 300ms，避免开头被切掉）；若是短噪声则 `ShortNoise` 丢弃；
- `active`：连续静音达 `end_silence_ms`（800ms）或超 `max_utterance` -> `SpeechEnded`。

**2. 会话状态机（`session.py:9-77`）** 用 `SessionPhase` 枚举严格管转换：`CONNECTED->IDLE->LISTENING->PROCESSING->SPEAKING->IDLE`，每个方法 `_require` 校验前置相位，非法转换直接抛 `InvalidStateError`。历史按偶数条裁剪（`finish_speaking`），保证 user/assistant 成对。

**3. 打断（barge-in）处理（`auto_voice_session.py:161` `abort`）**：固件发 `listen state:detect`（小智唤醒词检测）触发。区分两种情况很精细：
- `PROCESSING` 中断（还没出声）：没发过 `tts.start`，**不能发 `tts.stop`**，直接回 LISTENING；
- `SPEAKING` 中断（已在出声）：发 `tts.stop` 配对，并把**已生成的半截回答写进历史**（`voice_session.py:224` 的 `CancelledError` 分支），作为短期记忆。

**4. 延迟遥测（`voice_session.py:107-161`）**：每轮打 `turn_breakdown_ms` 日志，分解 `vad / asr / llm_first / tts_first / llm_total / tts_total / response_start`，`send_timing=True` 时还下发给客户端。注释里能看到这正是最近在优化的东西（见内存里的 latency plan）。

**5. TTS 限速（`voice_session.py:88-96`）**：`frame_interval` 模式下用 deadline-based 节拍防漂移，但**单向节流**--TTS 生成慢于实时时不拖慢，只压突发。

## 协议（`故事机协议.md` + `protocol/messages.py`）

文本帧走 UTF-8 JSON，二进制帧是裸 Opus 无头。上行 16 kHz、下行 24 kHz，都是单声道 60ms 帧。握手只认 V1 + opus + 16000 + mono + 60ms，其余直接关连接（`parse_hello`）。当前**无鉴权/无限流**（README "当前安全边界" 明说别直接上公网）。

## 客户端/联调工具

- `realtime_websocket_test.py`：麦克风实时联调客户端，支持 `--abort-after` 自动测试打断、各阶段耗时日志、指定音频设备；
- `firmware_sim.py`：固件模拟器；
- `websocket_test.py`：轻量测试。

## 当前状态

从 git 历史和未提交改动看，最近的工作集中在**延迟优化和打断联调**：服务端发 timing 消息、客户端加 abort 自动测试、VAD 端点静音时长的精确取值修正（`auto_voice_session.py:99-101` 的注释解释了旧墙钟算法吞掉 VAD 等待时间的 bug）。`docs/superpowers/` 下有完整的 plan/spec 流程记录，`docs/设计文档/` 里那份架构决策记录描述了更宏大的目标架构（三服务：ws-gateway / agent-worker / data-service，1000 在线、100 活跃、2 秒延迟预算）--当前代码是其中的实时语音核心。

需要我深入讲哪一块？比如 VAD 分句器的状态机细节、打断时序、延迟优化的具体策略，或者适配器层怎么对接 DashScope。
