# -*- coding: utf-8 -*-
"""核心智能体模块"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional
from io import BytesIO
from asyncio import Queue

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from Function_Call import ALL_FUNCTIONS
except ImportError:
    ALL_FUNCTIONS = {}

from src.core.intent import rule_based_intent_classify
from src.core.builder import MessageBuilder
from src.core.executor import ToolExecutor
from src.utils import AgentResponse, PerformanceMetrics, ToolCall
from src.services.tts import QwenTTSService, TTSConfig

try:
    import sounddevice as sd
    import numpy as np

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    np = None
    sd = None

PUNCTUATION_END = frozenset("。！？")
MAX_CHARS = 25


def _play_audio_sync(audio_data: bytes):
    """同步播放音频（完整播放，不中断）"""
    if not AUDIO_AVAILABLE or not audio_data:
        return
    try:
        import wave

        if audio_data[:4] != b"RIFF":
            return
        audio_stream = BytesIO(audio_data)
        with wave.open(audio_stream, "rb") as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            nframes = wf.getnframes()
            data = wf.readframes(nframes)
            if sample_width == 2:
                data = np.frombuffer(data, dtype=np.int16)
            elif sample_width == 4:
                data = np.frombuffer(data, dtype=np.int32)
            else:
                data = np.frombuffer(data, dtype=np.float32)
            if channels == 2:
                data = data.reshape(-1, 2)
            sd.play(data, framerate)
            sd.wait()
    except Exception:
        pass


class AudioPlayer:
    """音频播放器 - 从队列取音频，完整播放"""

    def __init__(self):
        self.queue: Queue = Queue()
        self.running = False

    async def start(self):
        """启动播放循环"""
        self.running = True
        asyncio.create_task(self._play_loop())

    async def stop(self):
        """停止播放"""
        await self.queue.put(None)
        self.running = False

    async def _play_loop(self):
        """播放循环 - 从队列取，完整播放"""
        while True:
            audio_data = await self.queue.get()
            if audio_data is None:
                break
            _play_audio_sync(audio_data)

    async def put(self, audio_data: bytes):
        """放入播放队列"""
        await self.queue.put(audio_data)


class TTSTask:
    """TTS任务 - TTS转换和播放完全并行"""

    def __init__(self, tts_service: QwenTTSService):
        self.tts_service = tts_service
        self.audio_player = AudioPlayer()
        self.buffer = ""
        self._total_audio_size = 0
        self._total_duration = 0

    async def start(self):
        """启动播放器"""
        await self.audio_player.start()

    def _should_trigger(self) -> bool:
        """检查是否应该触发TTS"""
        if not self.buffer:
            return False
        last_char = self.buffer[-1]
        last_ord = ord(last_char)
        if last_ord in {ord(p) for p in PUNCTUATION_END}:
            return True
        if len(self.buffer) >= MAX_CHARS:
            return True
        return False

    async def add_text(self, text: str):
        """添加文本到缓冲区，TTS转换和播放并行"""
        if not text:
            return
        self.buffer += text

        if self._should_trigger():
            text_to_synthesize = self.buffer
            self.buffer = ""

            result = await self.tts_service.synthesize(text_to_synthesize)
            if result.success and result.audio_data:
                self._total_audio_size += len(result.audio_data)
                self._total_duration += result.duration_ms
                await self.audio_player.put(result.audio_data)

    async def finish(self):
        """结束，播放剩余"""
        if self.buffer:
            result = await self.tts_service.synthesize(self.buffer)
            if result.success and result.audio_data:
                self._total_audio_size += len(result.audio_data)
                self._total_duration += result.duration_ms
                await self.audio_player.put(result.audio_data)
                self.buffer = ""

        await self.audio_player.stop()

    def get_stats(self) -> tuple:
        return self._total_audio_size, self._total_duration

    def get_result(self):
        from src.services.tts import TTSResult

        return TTSResult(
            audio_data=b"",
            duration_ms=self._total_duration,
            success=self._total_audio_size > 0,
            error_message=None if self._total_audio_size > 0 else "No audio generated",
        )


class DecoupledAgent:
    """
    解耦智能体
    架构：规则意图分类 -> 工具执行 -> 主模型流式回复
    """

    def __init__(
        self,
        main_model,
        tools: Optional[Dict[str, Callable]] = None,
        tts_config: Optional[TTSConfig] = None,
    ):
        self.main_model = main_model
        self.tool_executor = ToolExecutor(tools or ALL_FUNCTIONS)
        self.conversation_history: List[Dict] = []
        self.tts_service = QwenTTSService(tts_config)
        self.tts_enabled = self.tts_service.is_available()

    async def process(self, user_input: str, stream: bool = True) -> AgentResponse:
        """
        处理流程：
        1. 意图分类（规则，毫秒级）
        2. 工具执行（如需要）
        3. 主模型流式回复
        """
        metrics = PerformanceMetrics()
        metrics.set_tools_loaded_time(TOOLS_LOAD_DURATION_MS)
        metrics.set_program_start_time(PROGRAM_START)
        metrics.record("program_start")
        metrics.record("tools_loaded")

        print("[Stage 1] 意图分类中...")
        metrics.record("intent_classify_start")
        intent_result = rule_based_intent_classify(user_input)
        metrics.record("intent_classified")

        print(
            f"[OK] 意图: {intent_result.intent.value}, 置信度: {intent_result.confidence:.2f}"
        )
        print(f"    推理: {intent_result.reasoning}")
        if intent_result.suggested_tools:
            print(f"    建议工具: {intent_result.suggested_tools}")

        tool_calls: List[ToolCall] = []

        if intent_result.intent.value == "tool_call":
            print("[Stage 2] 执行工具...")

            tools_to_call = []
            for tool_name in intent_result.suggested_tools:
                if tool_name in self.tool_executor.functions:
                    tools_to_call.append(
                        {"name": tool_name, "arguments": intent_result.extracted_params}
                    )

            if tools_to_call:
                tool_calls = await self.tool_executor.execute_multiple(tools_to_call)
                metrics.record("tools_executed")

                print(f"[OK] 执行了 {len(tool_calls)} 个工具:")
                for tc in tool_calls:
                    print(f"    - {tc.tool_name}: {tc.duration_ms:.2f} ms")
            else:
                print("[WARN] 没有可用的工具")

        print("[Stage 3] 生成回复...")
        messages = MessageBuilder.build_main_model_messages(
            user_input, tool_calls, self.conversation_history
        )

        if stream:
            content = ""
            generation_start = time.time()
            first_token_received = False
            tts_task = None

            if self.tts_enabled:
                tts_task = TTSTask(self.tts_service)
                await tts_task.start()

            async for chunk in self.main_model.astream(messages):
                text = chunk.content if hasattr(chunk, "content") else str(chunk)
                content += text
                print(text, end="", flush=True)

                if not first_token_received:
                    first_token_time = (time.time() - generation_start) * 1000
                    metrics.set_first_token_time(first_token_time)
                    first_token_received = True

                if tts_task:
                    await tts_task.add_text(text)

            print()
            if tts_task:
                await tts_task.finish()
                tts_result = tts_task.get_result()
            else:
                tts_result = None
        else:
            generation_start = time.time()
            response = await self.main_model.ainvoke(messages)
            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            first_token_time = (time.time() - generation_start) * 1000
            metrics.set_first_token_time(first_token_time)

        metrics.record("response_generated")

        if tts_task:
            audio_size, duration = tts_task.get_stats()
            print(f"[OK] 流式TTS完成 (音频大小: {audio_size} bytes)")
            metrics.set_tts_time(duration)
        elif self.tts_enabled and content:
            print("[Stage 4] TTS语音合成...")
            tts_start = time.time()
            tts_result = await self.tts_service.synthesize(content)
            tts_duration = (time.time() - tts_start) * 1000
            metrics.set_tts_time(tts_duration)
            if tts_result.success:
                print(
                    f"[OK] TTS合成成功 (耗时: {tts_duration:.2f} ms, 音频大小: {len(tts_result.audio_data)} bytes)"
                )
            else:
                print(f"[WARN] TTS合成失败: {tts_result.error_message}")

        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": content})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        metrics.record("end")

        return AgentResponse(
            content=content,
            intent=intent_result.intent,
            tool_calls=tool_calls,
            metrics=metrics,
            message_history=self.conversation_history.copy(),
            tts_result=tts_result,
        )


PROGRAM_START = time.time()

try:
    TOOLS_LOAD_START = time.time()
    from Function_Call import ALL_TOOLS

    TOOLS_LOAD_END = time.time()
    TOOLS_LOAD_DURATION_MS = (TOOLS_LOAD_END - TOOLS_LOAD_START) * 1000
    TOOLS_LOADED_TIME = time.time()
    print(
        f"[OK] 成功加载 {len(ALL_TOOLS)} 个工具 (耗时: {TOOLS_LOAD_DURATION_MS:.2f} ms)"
    )
except ImportError as e:
    print(f"[ERROR] 加载工具失败: {e}")
    ALL_TOOLS = []
    TOOLS_LOAD_DURATION_MS = 0.0
    TOOLS_LOADED_TIME = time.time()
