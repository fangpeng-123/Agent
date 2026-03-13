# -*- coding: utf-8 -*-
"""
Streaming TTS Service - 新版真正流式TTS服务
基于 streaming_tts 模块实现
"""

from .streaming_tts.service import StreamingTTSService as _InnerService
from .streaming_tts.provider import StreamingTTSConfig

import os
import time
from dataclasses import dataclass
from typing import Optional, AsyncGenerator, Callable


# 兼容别名
TTSConfig = StreamingTTSConfig


@dataclass
class StreamingTTSResult:
    """TTS 结果"""

    audio_data: bytes = b""
    duration_ms: float = 0
    success: bool = False
    error_message: Optional[str] = None
    first_audio_delay: float = 0


class StreamingTTSService:
    """
    新版真正流式 TTS 服务

    特点：
    - 真正的流式合成（边发送边接收）
    - 低首字延迟（<100ms）

    与旧版 tts_service 的区别：
    - 旧版：累积文本 → 整段合成 → 返回
    - 新版：发送文本 → 边接收音频块 → 边返回
    """

    VOICES = _InnerService.VOICES

    def __init__(self, config: Optional[StreamingTTSConfig] = None):
        self.config = config or StreamingTTSConfig()
        self._inner = _InnerService(self.config)

    def is_available(self) -> bool:
        return self._inner.is_available()

    async def synthesize_stream(
        self,
        text: str,
        on_audio: Optional[Callable[[bytes, str], None]] = None,
    ) -> AsyncGenerator[tuple[bytes, str], None]:
        """
        流式合成音频

        Args:
            text: 要合成的文本
            on_audio: 音频回调函数

        Yields:
            (audio_data, text_segment) 元组
        """
        async for result in self._inner.synthesize_stream(text, on_audio):
            yield result

    async def process_llm_stream(
        self,
        llm_stream: AsyncGenerator[str, None],
        on_audio: Optional[Callable[[bytes, str], None]] = None,
    ) -> AsyncGenerator[tuple[bytes, str], None]:
        """
        处理 LLM 流式输出并生成音频流

        Args:
            llm_stream: LLM 文本流
            on_audio: 音频回调函数

        Yields:
            (audio_data, text_segment) 元组
        """
        async for result in self._inner.process_llm_stream(llm_stream, on_audio):
            yield result

    async def synthesize(self, text: str) -> StreamingTTSResult:
        """
        合成完整音频

        Args:
            text: 要合成的文本

        Returns:
            StreamingTTSResult
        """
        return await self._inner.synthesize(text)

    async def synthesize_to_file(self, text: str, file_path: str) -> StreamingTTSResult:
        """合成音频并保存到文件"""
        result = await self.synthesize(text)

        if result.success:
            os.makedirs(
                os.path.dirname(file_path) if os.path.dirname(file_path) else ".",
                exist_ok=True,
            )
            with open(file_path, "wb") as f:
                f.write(result.audio_data)

        return result

    @classmethod
    def get_available_voices(cls) -> dict:
        return cls.VOICES.copy()

    def play_pcm_audio(
        self,
        audio_data: bytes,
        sample_rate: int = 24000,
        channels: int = 1,
        bits_per_sample: int = 16,
    ) -> bool:
        """播放 PCM 音频数据"""
        return self._inner.play_pcm_audio(
            audio_data, sample_rate, channels, bits_per_sample
        )
