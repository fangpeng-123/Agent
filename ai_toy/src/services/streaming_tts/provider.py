# -*- coding: utf-8 -*-
"""
Streaming TTS Provider - 真正的流式TTS提供者
基于阿里云 WebSocket 实时 API 实现
"""

import os
import base64
import asyncio
import threading
import time
from pathlib import Path
from typing import AsyncGenerator, Optional, Callable
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    import dashscope
    from dashscope.audio.qwen_tts_realtime import (
        QwenTtsRealtime,
        AudioFormat,
    )

    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    dashscope = None
    QwenTtsRealtime = None
    AudioFormat = None


@dataclass
class StreamingTTSConfig:
    """Streaming TTS 配置"""

    model: str = "qwen3-tts-flash-realtime"
    voice: str = "Cherry"
    sample_rate: int = 24000
    speed: float = 1.0
    api_key: str = ""


class StreamingCallback:
    """流式回调处理器"""

    def __init__(self):
        self.audio_chunks: list[bytes] = []
        self.complete_event = threading.Event()
        self.error_msg: str = ""
        self.session_id: str = ""
        self.first_audio_time: float = 0
        self._first_audio_recorded = False

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
                if not self._first_audio_recorded:
                    self.first_audio_time = time.time()
                    self._first_audio_recorded = True

                recv_audio_b64 = message.get("delta", "")
                if recv_audio_b64:
                    audio_data = base64.b64decode(recv_audio_b64)
                    self.audio_chunks.append(audio_data)

            elif "session.finished" == event_type:
                self.complete_event.set()
        except Exception as e:
            self.error_msg = str(e)
            self.complete_event.set()


class StreamingTTSProvider:
    """
    真正的流式 TTS 提供者

    与传统累积式TTS的区别：
    - 传统：累积一段文本 → 发送 → 等待整段返回 → 播放
    - 流式：发送文本 → 边接收音频块 → 边播放（低延迟）

    特点：
    - 保持WebSocket长连接
    - 实时发送文本，实时接收音频
    - 首字延迟 < 100ms
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

    def __init__(self, config: Optional[StreamingTTSConfig] = None):
        self.config = config or StreamingTTSConfig()
        self._load_api_key()
        self._tts_instance: Optional[QwenTtsRealtime] = None
        self._callback: Optional[StreamingCallback] = None
        self._connected = False
        self._lock = threading.Lock()

    def _load_api_key(self):
        """加载 API 密钥"""
        if not self.config.api_key:
            env_path = Path(__file__).parent.parent / ".env"
            if env_path.exists():
                load_dotenv(dotenv_path=str(env_path), override=True)
            self.config.api_key = os.getenv("DASHSCOPE_API_KEY", "")

        if DASHSCOPE_AVAILABLE and self.config.api_key:
            if dashscope is not None:
                dashscope.api_key = self.config.api_key

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return DASHSCOPE_AVAILABLE and bool(self.config.api_key)

    def _get_audio_format(self):
        """获取音频格式"""
        if AudioFormat is None:
            return None
        return AudioFormat.PCM_24000HZ_MONO_16BIT

    def connect(self) -> bool:
        """
        建立 WebSocket 连接（长连接）

        Returns:
            连接是否成功
        """
        if not self.is_available():
            print("[StreamingTTS] DashScope SDK 未安装或未设置 API Key")
            return False

        if self._connected and self._tts_instance:
            return True

        try:
            self._callback = StreamingCallback()
            self._tts_instance = QwenTtsRealtime(
                model=self.config.model,
                callback=self._callback,
                url="wss://dashscope.aliyuncs.com/api-ws/v1/realtime",
            )

            self._tts_instance.connect()

            # 配置会话参数
            audio_format = self._get_audio_format()
            if audio_format is not None:
                self._tts_instance.update_session(
                    voice=self.config.voice,
                    response_format=audio_format,
                    mode="server_commit",
                    speed=self.config.speed,
                )

            self._connected = True
            print(f"[StreamingTTS] WebSocket 连接已建立")
            return True

        except Exception as e:
            print(f"[StreamingTTS] 连接失败: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """断开连接"""
        if self._tts_instance:
            try:
                self._tts_instance.finish()
            except Exception:
                pass
        self._connected = False
        self._tts_instance = None

    def _create_callback(self) -> StreamingCallback:
        """创建回调处理器"""
        return StreamingCallback()

    def _create_tts_instance(self, callback: StreamingCallback):
        """创建 TTS 实例"""
        return QwenTtsRealtime(
            model=self.config.model,
            callback=callback,
            url="wss://dashscope.aliyuncs.com/api-ws/v1/realtime",
        )

    def synthesize_streaming(
        self,
        text: str,
        on_chunk: Optional[Callable[[bytes, str], None]] = None,
    ) -> AsyncGenerator[tuple[bytes, str], None]:
        """
        流式合成音频

        与传统方式的区别：
        - 传统：发送整段文本，等待全部返回，再 yield
        - 流式：发送文本后立即 yield 收到的音频块

        Args:
            text: 要合成的文本
            on_chunk: 音频块回调（可选）

        Yields:
            (audio_chunk, text) 元组
        """
        if not self.is_available():
            return

        # 确保连接已建立
        if not self._connected:
            if not self.connect():
                return

        # 重置回调，准备新的合成
        self._callback = StreamingCallback()

        try:
            # 发送文本
            self._tts_instance.append_text(text)
            self._tts_instance.finish()

            # 等待完成，同时实时 yield 音频块
            while not self._callback.complete_event.is_set():
                time.sleep(0.05)  # 50ms 检查一次

                # 如果有新音频块，立即返回
                if self._callback.audio_chunks:
                    while self._callback.audio_chunks:
                        chunk = self._callback.audio_chunks.pop(0)
                        if chunk:
                            if on_chunk:
                                on_chunk(chunk, text)
                            yield (chunk, text)

            # 处理剩余的音频块
            while self._callback.audio_chunks:
                chunk = self._callback.audio_chunks.pop(0)
                if chunk:
                    if on_chunk:
                        on_chunk(chunk, text)
                    yield (chunk, text)

            if self._callback.error_msg:
                print(f"[StreamingTTS] 合成错误: {self._callback.error_msg}")

        except Exception as e:
            print(f"[StreamingTTS] 流式合成异常: {e}")
            self._connected = False

    def synthesize(self, text: str) -> bytes:
        """
        同步合成完整音频

        Args:
            text: 要合成的文本

        Returns:
            完整的音频数据
        """
        audio_data = bytearray()

        for chunk, _ in self.synthesize_streaming(text):
            audio_data.extend(chunk)

        return bytes(audio_data)

    @classmethod
    def get_available_voices(cls) -> dict:
        """获取可用音色"""
        return cls.VOICES.copy()
