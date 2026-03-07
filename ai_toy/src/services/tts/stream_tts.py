# -*- coding: utf-8 -*-
"""
流式 TTS 协调器
协调 LLM 流式输出和 TTS 流式合成
"""

import asyncio
import time
from typing import AsyncGenerator, Callable, Optional, Any
from concurrent.futures import ThreadPoolExecutor

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

from .base import TTSProviderBase, TTSMessage, ContentType


def _apply_fade_out(audio_data: bytes, fade_samples: int = 480) -> bytes:
    """末尾淡出处理，防止爆音"""
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


class StreamTTS:
    """
    流式 TTS 协调器

    协调 LLM 流式输出和 TTS 流式合成：
    1. 同时启动两个并发任务：
       - feed_llm_stream(): 消费 LLM 流，将文本放入队列
       - get_audio_stream(): 从队列获取音频，立即 yield
    2. 使用 ThreadPoolExecutor 处理阻塞的 TTS API 调用
    """

    def __init__(self, provider: TTSProviderBase):
        """
        初始化流式 TTS 协调器

        Args:
            provider: TTS 提供者实例
        """
        self.provider = provider
        self._executor = ThreadPoolExecutor(max_workers=2)

    async def process_llm_stream(
        self,
        llm_stream: AsyncGenerator[str, None],
        on_audio: Optional[Callable[[bytes, str], None]] = None,
    ) -> AsyncGenerator[tuple[bytes, str], None]:
        """
        处理 LLM 流式输出并生成音频流

        Args:
            llm_stream: LLM 文本流
            on_audio: 音频回调函数（可选）

        Yields:
            (audio_data, text) 元组
        """
        self.provider.reset()
        self.provider.start()

        feed_done = asyncio.Event()

        async def feed_llm_stream():
            """消费 LLM 流，将文本放入队列"""
            try:
                async for text_chunk in llm_stream:
                    if text_chunk:
                        self.provider.put_text(text_chunk)
            except Exception as e:
                self.provider.tts_audio_queue.put(
                    TTSMessage(content_type=ContentType.ERROR, error=str(e))
                )
            finally:
                self.provider.finish_text()
                feed_done.set()

        feed_task = asyncio.create_task(feed_llm_stream())

        try:
            while True:
                message = await asyncio.get_event_loop().run_in_executor(
                    self._executor, self.provider.get_audio, 30.0
                )

                if message is None:
                    if feed_done.is_set():
                        break
                    continue

                if message.content_type == ContentType.END:
                    break

                if message.content_type == ContentType.ERROR:
                    print(f"[StreamTTS Error] {message.error}")
                    continue

                if message.content_type == ContentType.AUDIO:
                    if message.audio_data:
                        audio_with_fade = _apply_fade_out(message.audio_data)
                        if on_audio:
                            on_audio(audio_with_fade, message.text)
                        yield (audio_with_fade, message.text)

        finally:
            feed_task.cancel()
            try:
                await feed_task
            except asyncio.CancelledError:
                pass
            self.provider.stop()

    async def process_text(
        self,
        text: str,
        on_audio: Optional[Callable[[bytes, str], None]] = None,
    ) -> AsyncGenerator[tuple[bytes, str], None]:
        """
        处理单个文本并生成音频流

        Args:
            text: 要合成的文本
            on_audio: 音频回调函数（可选）

        Yields:
            (audio_data, text) 元组
        """
        self.provider.reset()
        self.provider.start()

        self.provider.put_text(text)
        self.provider.finish_text()

        try:
            while True:
                message = await asyncio.get_event_loop().run_in_executor(
                    self._executor, self.provider.get_audio, 30.0
                )

                if message is None:
                    break

                if message.content_type == ContentType.END:
                    break

                if message.content_type == ContentType.ERROR:
                    print(f"[StreamTTS Error] {message.error}")
                    continue

                if message.content_type == ContentType.AUDIO:
                    if message.audio_data:
                        if on_audio:
                            on_audio(message.audio_data, message.text)
                        yield (message.audio_data, message.text)

        finally:
            self.provider.stop()

    def shutdown(self):
        """关闭协调器"""
        self._executor.shutdown(wait=False)


class StreamTTSManager:
    """
    流式 TTS 管理器

    管理 StreamTTS 实例的创建和复用
    """

    _instance: Optional["StreamTTSManager"] = None

    def __init__(self, provider: Optional[TTSProviderBase] = None):
        self._provider = provider
        self._stream_tts: Optional[StreamTTS] = None

    @classmethod
    def get_instance(
        cls, provider: Optional[TTSProviderBase] = None
    ) -> "StreamTTSManager":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(provider)
        return cls._instance

    def get_stream_tts(self, provider: Optional[TTSProviderBase] = None) -> StreamTTS:
        """
        获取 StreamTTS 实例

        Args:
            provider: TTS 提供者（可选，如果提供则更新）

        Returns:
            StreamTTS 实例
        """
        if provider:
            self._provider = provider

        if self._provider is None:
            raise ValueError("TTS Provider 未设置")

        if self._stream_tts is None:
            self._stream_tts = StreamTTS(self._provider)

        return self._stream_tts

    def shutdown(self):
        """关闭管理器"""
        if self._stream_tts:
            self._stream_tts.shutdown()
            self._stream_tts = None
