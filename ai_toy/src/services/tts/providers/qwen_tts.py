# -*- coding: utf-8 -*-
"""
通义千问流式 TTS 提供者
实现真正的流式音频合成
"""

import os
import base64
import asyncio
import threading
import time
from pathlib import Path
from typing import AsyncGenerator, Any, Optional
from dotenv import load_dotenv

from ..base import TTSProviderBase, TTSMessage, ContentType

try:
    import dashscope
    from dashscope.audio.qwen_tts_realtime import (
        QwenTtsRealtime,
        QwenTtsRealtimeCallback,
        AudioFormat,
    )

    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    dashscope = None
    QwenTtsRealtime = None
    QwenTtsRealtimeCallback = None
    AudioFormat = None


class StreamingCallback:
    """流式回调处理器"""

    def __init__(self):
        self.audio_chunks: list[bytes] = []
        self.complete_event = threading.Event()
        self.error_msg: str = ""
        self.session_id: str = ""
        self._first_audio_time: Optional[float] = None

    def on_open(self) -> None:
        pass

    def on_close(self, close_status_code, close_msg) -> None:
        pass

    def on_event(self, message: dict) -> None:
        try:
            event_type = message.get("type", "")
            if "session.created" == event_type:
                self.session_id = message.get("session", {}).get("id", "")
            elif "response.audio.delta" == event_type:
                # 记录首音频时间
                if self._first_audio_time is None:
                    self._first_audio_time = time.time()
                recv_audio_b64 = message.get("delta", "")
                if recv_audio_b64:
                    audio_data = base64.b64decode(recv_audio_b64)
                    self.audio_chunks.append(audio_data)
            elif "session.finished" == event_type:
                self.complete_event.set()
        except Exception as e:
            self.error_msg = str(e)
            self.complete_event.set()


class QwenTTSProvider(TTSProviderBase):
    """
    通义千问流式 TTS 提供者

    继承 TTSProviderBase，实现真正的流式音频合成
    支持连接复用以减少段间停顿
    """

    VOICES = {
        "Seren": "女声-通用",
        "Cherry": "女声-活泼",
        "Xi": "男声-新闻",
        "Yaqi": "男声-故事",
        "Aiya": "女声-直播",
        "Xiaoxian": "女声-儿童",
        "Ethan": "男声-教育",
        "Liam": "男声-专业",
    }

    def __init__(
        self,
        model: str = "qwen3-tts-flash-realtime",
        voice: str = "Cherry",
        sample_rate: int = 24000,
        speed: float = 1.0,
        api_key: str = "",
    ):
        super().__init__()
        self.model = model
        self.voice = voice
        self.sample_rate = sample_rate
        self.speed = speed
        self.api_key = api_key
        # 连接复用
        self._tts_instance: Any = None
        self._callback: Any = None
        self._connection_lock = threading.Lock()
        self._first_audio_delay: float = 0
        self._load_api_key()

    def _load_api_key(self):
        """加载 API 密钥"""
        if not self.api_key:
            env_path = Path(__file__).parent.parent.parent / ".env"
            if env_path.exists():
                load_dotenv(dotenv_path=str(env_path), override=True)
            self.api_key = os.getenv("DASHSCOPE_API_KEY", "")

        if DASHSCOPE_AVAILABLE and self.api_key:
            if dashscope is not None:
                dashscope.api_key = self.api_key

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return DASHSCOPE_AVAILABLE and bool(self.api_key)

    def _get_audio_format(self) -> Any:
        """获取音频格式"""
        if AudioFormat is None:
            return None
        return AudioFormat.PCM_24000HZ_MONO_16BIT

    def _ensure_connection(self):
        """确保 WebSocket 连接存在（连接复用）"""
        if self._tts_instance is None:
            with self._connection_lock:
                if self._tts_instance is None:
                    self._callback = StreamingCallback()
                    self._tts_instance = QwenTtsRealtime(
                        model=self.model,
                        callback=self._callback,  # type: ignore[arg-type]
                        url="wss://dashscope.aliyuncs.com/api-ws/v1/realtime",
                    )
                    self._tts_instance.connect()
                    audio_format = self._get_audio_format()
                    if audio_format is not None:
                        self._tts_instance.update_session(
                            voice=self.voice,
                            response_format=audio_format,
                            mode="server_commit",
                            speed=self.speed,
                        )
        # 返回建立的连接
        return self._tts_instance

    def close_connection(self):
        """关闭 WebSocket 连接"""
        with self._connection_lock:
            if self._tts_instance:
                try:
                    self._tts_instance = None
                except Exception:
                    pass
                self._callback = None

    async def _stream_tts_impl(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        流式 TTS 实现 - 支持连接复用

        Args:
            text: 要合成的文本

        Yields:
            音频数据块（bytes）
        """
        if not self.is_available():
            raise RuntimeError("DashScope SDK 未安装或未设置 DASHSCOPE_API_KEY")

        if QwenTtsRealtime is None:
            raise RuntimeError("QwenTtsRealtime 不可用")

        start_time = time.time()
        loop = asyncio.get_running_loop()

        # 每次发送新文本前，确保连接存在
        await loop.run_in_executor(None, self._ensure_connection)

        def sync_synthesize():
            # 使用已建立的连接
            if self._callback:
                # 重置状态
                self._callback.audio_chunks.clear()
                self._callback.complete_event.clear()
                self._callback.error_msg = ""
                self._callback._first_audio_time = None

            # 发送文本
            self._tts_instance.append_text(text)
            self._tts_instance.finish()

            # 等待完成
            if self._callback:
                self._callback.complete_event.wait(timeout=60)

        # 在线程中执行
        await loop.run_in_executor(None, sync_synthesize)

        # 记录首音频延迟
        if self._callback and self._callback._first_audio_time:
            self._first_audio_delay = (
                self._callback._first_audio_time - start_time
            ) * 1000

        if self._callback and self._callback.error_msg:
            raise RuntimeError(f"TTS 合成错误: {self._callback.error_msg}")

        # 返回所有音频块
        for chunk in self._callback.audio_chunks if self._callback else []:
            if chunk:
                yield chunk

    async def synthesize(self, text: str) -> bytes:
        """
        合成完整音频

        Args:
            text: 要合成的文本

        Returns:
            完整的音频数据
        """
        audio_data = bytearray()
        async for chunk in self._stream_tts_impl(text):
            audio_data.extend(chunk)
        return bytes(audio_data)

    @classmethod
    def get_available_voices(cls) -> dict:
        """获取可用音色"""
        return cls.VOICES.copy()
