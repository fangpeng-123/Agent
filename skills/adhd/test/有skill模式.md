# 故事机语音交互服务 - 代码讲解

已经把核心代码读完了。下面按"是什么 -> 架构分层 -> 一轮对话数据流 -> 关键设计点"讲。

## 这是什么

故事机语音交互服务。ESP32 固件通过 WebSocket 连上来,持续上传裸 Opus 音频;服务端做 **VAD 切分 -> ASR -> LLM -> TTS**,再把合成的 Opus 流回去。同一连接支持多轮上下文。

技术栈:FastAPI + uvicorn + DashScope(阿里云 ASR/LLM/TTS)+ WebRTC VAD + PyAV(Opus 编解码)。

## 架构分层(端口与适配器 / clean architecture)

```
src/story_player/
├── ports/ai.py        # 抽象接口:SpeechRecognizer / LanguageModel / SpeechSynthesizer / ProviderBundle
├── adapters/          # DashScope 实现(asr/llm/tts)+ factory 组装
├── application/       # 核心业务逻辑(不依赖 I/O)
│   ├── auto_voice_session.py   # 会话编排器:收 PCM、驱动 VAD、起后台轮次、处理 abort
│   ├── voice_session.py        # 一轮对话:ASR 收尾 -> LLM 流式 -> TTS 流式 + 耗时打点
│   └── utterance.py            # VAD 分段状态机:idle->candidate->active
├── protocol/          # messages(hello/stt/tts/listen-detect 解析)+ session(SessionPhase 状态机)
├── api/websocket.py   # WebSocket 端点,把上面几层串起来
├── audio/             # opus 解码 + vad 检测器
├── config.py          # pydantic-settings,全部 VAD/模型参数走 .env
└── main.py            # FastAPI app 工厂 + 默认装配
```

依赖方向:`api -> application -> ports ← adapters`。核心逻辑 `application/` 只认 Protocol 接口,不碰 DashScope,所以测试能用 Fake Provider 跑(`tests/` 镜像 src 结构)。

## 一轮对话数据流

```
固件 hello(v1)
  -> api/websocket.py 解析 hello、建 VoiceSessionState、回 server_hello(+session_id)
固件持续上传 16kHz/单声道/60ms 裸 Opus
  -> websocket.py: Opus 解码成 PCM -> AutoVoiceSession.handle_pcm(pcm)
  -> UtteranceSegmenter.feed_pcm: VAD 状态机吃帧,吐事件
       SpeechStarted -> 建 ASR、asr.start、喂缓冲的 preroll PCM
       SpeechAudio   -> 持续喂 ASR
       SpeechEnded   -> finish_listening,起后台任务 _run_turn
  -> VoiceTurnService.run_turn(在后台 asyncio.Task 里):
       asr.finish() 拿用户文本 -> 发 stt 消息
       llm.stream():流式收 chunk,按句号/问号/感叹号切句,凑齐一句立刻 stream_tts
       tts.start(首句前)-> 逐包发 24kHz Opus -> tts.stop
       finish_speaking:用户+助手文本入历史(history_limit 滚动)
  -> 回 LISTENING,等下一轮
```

关键:`SpeechEnded` 触发的轮次跑在**后台 Task** 里,主接收循环不等它,所以下一轮音频能继续收(或被 abort)。

## 关键设计点

- **服务端 VAD**:固件不发包络控制(listen.start/stop),只管持续上传;起止全靠 `UtteranceSegmenter` 判定。分段器三态 `idle->candidate->active`,有 preroll 预滚(保留说话前 300ms)、min_speech(过滤短噪声)、end_silence(800ms 静音断句)。

- **SessionPhase 状态机**(`protocol/session.py`):`CONNECTED->IDLE->LISTENING->PROCESSING->SPEAKING->IDLE`,每个转移都有 `_require` 校验,非法转移抛 `InvalidStateError`。

- **流式低延迟**:LLM 边出边切句,TTS 凑齐第一句就 `tts.start` 并发包,不等整句生成完。`run_turn` 里 `response_start = vad + asr + llm_first + tts_first` 是核心延迟指标。

- **abort 打断**(`AutoVoiceSession.abort`):收到 `listen state:detect` -> cancel 后台轮次。**按相位决定是否补 tts.stop**:PROCESSING(还没出声)不补、SPEAKING/IDLE(已发 tts.start)补 stop。被打断的半截回答会写进历史做短期记忆。

- **TTS 限速**(`frame_interval`):deadline-based 节拍,防止单句 TTS 突发下发撑爆固件缓冲;只单向节流(TTS 慢于实时时不拖)。

- **timing 遥测**:`main.py` 开了 `send_timing=True`,每轮结束发 `timing` 消息,含 vad/asr/llm_first/tts_first 各段耗时,客户端打印分解。

## 入口与外围脚本

- 启动服务:`uvicorn story_player.main:app --app-dir src --port 8000 --ws-ping-interval 0`(关 ping,防 ESP32 空闲不回 pong 被断)
- `realtime_websocket_test.py`:本机麦克风联调客户端(录->上传->收 TTS 播放)
- `firmware_sim.py`:固件模拟器
- 测试:`pytest -v`,用 Fake Provider 不调真实 DashScope

---

当前 git 上有一批未提交改动集中在 **abort 打断 + timing 分解**(`voice_session.py`、`auto_voice_session.py`、协议消息、对应测试),还有两份新文档 `2026-07-28-defining-products` 在规划产品定义。
