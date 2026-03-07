# -*- coding: utf-8 -*-
"""
通义千问实时 TTS 语音合成服务

提供两种使用方式：
1. QwenTTSService - 简单的 TTS 服务（向后兼容）
2. StreamTTSService - 流式 TTS 服务（推荐）
"""

import os
import base64
import threading
import time
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, AsyncGenerator, Callable
from dotenv import load_dotenv

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

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
    QwenTtsRealtime = None
    QwenTtsRealtimeCallback = None
    AudioFormat = None
    dashscope = None


def _apply_fade_out(audio_data: bytes, fade_samples: int = 480) -> bytes:
    """末尾淡出处理，防止爆音

    Args:
        audio_data: PCM音频数据
        fade_samples: 淡出采样点数，约20ms (480@24kHz)

    Returns:
        处理后的音频数据
    """
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


from .tts.base import TTSProviderBase, TTSMessage, ContentType
from .tts.stream_tts import StreamTTS, StreamTTSManager
from .tts.providers.qwen_tts import QwenTTSProvider


@dataclass
class TTSConfig:
    """TTS 配置"""

    api_key: str = ""
    model: str = "qwen3-tts-flash-realtime"
    voice: str = "Cherry"
    response_format: str = "pcm"
    sample_rate: int = 24000
    mode: str = "server_commit"
    speed: float = 1.0


@dataclass
class TTSResult:
    """TTS 结果"""

    audio_data: bytes = b""
    duration_ms: float = 0
    success: bool = False
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    first_audio_delay: float = 0


class MyCallback:
    """兼容性回调类"""

    def __init__(self):
        self.complete_event = threading.Event()
        self.audio_data = bytearray()
        self.session_id: Optional[str] = None
        self.first_audio_delay: float = 0

    def on_open(self) -> None:
        print("[TTS] connection opened")

    def on_close(self, close_status_code, close_msg) -> None:
        print(
            f"[TTS] connection closed with code: {close_status_code}, msg: {close_msg}"
        )

    def on_event(self, message: dict) -> None:
        try:
            event_type = message.get("type", "")
            if "session.created" == event_type:
                self.session_id = message.get("session", {}).get("id", "")
                print(f"[TTS] session created: {self.session_id}")
            elif "response.audio.delta" == event_type:
                recv_audio_b64 = message.get("delta", "")
                audio_data = base64.b64decode(recv_audio_b64)
                self.audio_data.extend(audio_data)
            elif "response.done" == event_type:
                print("[TTS] response done")
            elif "session.finished" == event_type:
                print("[TTS] session finished")
                self.complete_event.set()
        except Exception as e:
            print(f"[TTS Error] {e}")

    def wait_for_finished(self, timeout: float = 30) -> bool:
        return self.complete_event.wait(timeout=timeout)


class QwenTTSService:
    """
    通义千问实时 TTS 服务（向后兼容版本）

    推荐使用 StreamTTSService 获得更好的流式体验
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

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._load_api_key()
        self._tts_instance = None
        self._callback = None

    def _load_api_key(self):
        script_dir = Path(__file__).parent
        env_path = script_dir / ".env"

        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path), override=True)

        self.config.api_key = self.config.api_key or os.getenv("DASHSCOPE_API_KEY", "")

        if DASHSCOPE_AVAILABLE and self.config.api_key:
            dashscope.api_key = self.config.api_key

    def is_available(self) -> bool:
        if not DASHSCOPE_AVAILABLE:
            return False
        if not self.config.api_key:
            return False
        return True

    def _get_audio_format(self):
        if AudioFormat is None:
            return None
        return AudioFormat.PCM_24000HZ_MONO_16BIT

    async def synthesize(self, text: str) -> TTSResult:
        if not self.is_available():
            return TTSResult(
                success=False,
                error_message="DashScope SDK 未安装或未设置 DASHSCOPE_API_KEY",
            )

        start_time = time.time()
        self._callback = MyCallback()

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._run_tts_sync, text)
        except Exception as e:
            return TTSResult(
                success=False,
                error_message=f"TTS 调用失败: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

        result = TTSResult(
            audio_data=_apply_fade_out(bytes(self._callback.audio_data)),
            duration_ms=(time.time() - start_time) * 1000,
            success=len(self._callback.audio_data) > 0,
            session_id=self._callback.session_id,
            first_audio_delay=self._callback.first_audio_delay,
        )

        if not result.success:
            result.error_message = "音频数据为空"

        return result

    def _run_tts_sync(self, text: str):
        if QwenTtsRealtime is None:
            raise RuntimeError("QwenTtsRealtime 不可用")

        self._tts_instance = QwenTtsRealtime(
            model=self.config.model,
            callback=self._callback,
            url="wss://dashscope.aliyuncs.com/api-ws/v1/realtime",
        )

        self._tts_instance.connect()
        self._tts_instance.update_session(
            voice=self.config.voice,
            response_format=self._get_audio_format(),
            mode=self.config.mode,
            speed=self.config.speed,
        )

        self._tts_instance.append_text(text)
        self._tts_instance.finish()
        self._callback.wait_for_finished()

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        if not self.is_available():
            return

        self._callback = MyCallback()
        if QwenTtsRealtime is None:
            return

        self._tts_instance = QwenTtsRealtime(
            model=self.config.model,
            callback=self._callback,
            url="wss://dashscope.aliyuncs.com/api-ws/v1/realtime",
        )

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._tts_instance.connect)

        self._tts_instance.update_session(
            voice=self.config.voice,
            response_format=self._get_audio_format(),
            mode=self.config.mode,
            speed=self.config.speed,
        )

        self._tts_instance.append_text(text)
        self._tts_instance.finish()

        while not self._callback.complete_event.is_set():
            await asyncio.sleep(0.05)

        yield bytes(self._callback.audio_data)

    async def synthesize_to_file(self, text: str, file_path: str) -> TTSResult:
        result = await self.synthesize(text)

        if result.success:
            os.makedirs(
                os.path.dirname(file_path) if os.path.dirname(file_path) else ".",
                exist_ok=True,
            )
            with open(file_path, "wb") as f:
                f.write(result.audio_data)

        return result

    def get_available_voices(self) -> dict:
        return self.VOICES

    def play_pcm_audio(
        self,
        audio_data: bytes,
        sample_rate: int = 24000,
        channels: int = 1,
        bits_per_sample: int = 16,
    ) -> bool:
        """播放 PCM 音频数据"""
        try:
            import pyaudio

            format_map = {8: pyaudio.paUInt8, 16: pyaudio.paInt16, 32: pyaudio.paInt32}
            audio_format = format_map.get(bits_per_sample, pyaudio.paInt16)

            p = pyaudio.PyAudio()
            stream = p.open(
                format=audio_format,
                channels=channels,
                rate=sample_rate,
                output=True,
            )
            print("[TTS] 正在播放音频...")
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("[TTS] 播放完成")
            return True
        except ImportError:
            print("[TTS] 警告: 未安装 pyaudio，请运行: pip install pyaudio")
            return False
        except Exception as e:
            print(f"[TTS] 警告: 播放失败: {e}")
            return False


class StreamTTSService:
    """
    流式 TTS 服务（推荐）

    特点：
    - 双队列缓冲机制
    - 智能文本分割（第一句遇逗号即合成）
    - 真正的流式输出
    - 低延迟首音响应
    """

    VOICES = QwenTTSProvider.VOICES

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._provider: Optional[QwenTTSProvider] = None
        self._stream_tts: Optional[StreamTTS] = None

    def _get_provider(self) -> QwenTTSProvider:
        """获取或创建 TTS 提供者"""
        if self._provider is None:
            self._provider = QwenTTSProvider(
                model=self.config.model,
                voice=self.config.voice,
                sample_rate=self.config.sample_rate,
                speed=self.config.speed,
                api_key=self.config.api_key,
            )
        return self._provider

    def is_available(self) -> bool:
        return self._get_provider().is_available()

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
        if not self.is_available():
            return

        provider = self._get_provider()
        stream_tts = StreamTTS(provider)

        async for audio_data, text_segment in stream_tts.process_text(text, on_audio):
            yield (audio_data, text_segment)

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
        if not self.is_available():
            return

        provider = self._get_provider()
        stream_tts = StreamTTS(provider)

        async for audio_data, text_segment in stream_tts.process_llm_stream(
            llm_stream, on_audio
        ):
            yield (audio_data, text_segment)

    async def synthesize(self, text: str) -> TTSResult:
        """
        合成完整音频

        Args:
            text: 要合成的文本

        Returns:
            TTSResult
        """
        start_time = time.time()
        audio_data = bytearray()

        async for chunk, _ in self.synthesize_stream(text):
            audio_data.extend(chunk)

        result = TTSResult(
            audio_data=bytes(audio_data),
            duration_ms=(time.time() - start_time) * 1000,
            success=len(audio_data) > 0,
        )

        if not result.success:
            result.error_message = "音频数据为空"

        return result

    async def synthesize_to_file(self, text: str, file_path: str) -> TTSResult:
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
        try:
            import pyaudio

            format_map = {8: pyaudio.paUInt8, 16: pyaudio.paInt16, 32: pyaudio.paInt32}
            audio_format = format_map.get(bits_per_sample, pyaudio.paInt16)

            p = pyaudio.PyAudio()
            stream = p.open(
                format=audio_format,
                channels=channels,
                rate=sample_rate,
                output=True,
            )
            print("[TTS] 正在播放音频...")
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("[TTS] 播放完成")
            return True
        except ImportError:
            print("[TTS] 警告: 未安装 pyaudio，请运行: pip install pyaudio")
            return False
        except Exception as e:
            print(f"[TTS] 警告: 播放失败: {e}")
            return False


async def test_stream_tts():
    """测试流式 TTS 服务"""
    print("\n" + "=" * 60)
    print("[INFO] 流式 TTS 服务测试")
    print("=" * 60)

    config = TTSConfig(
        model="qwen3-tts-flash-realtime",
        voice="Cherry",
        speed=1.0,
    )

    service = StreamTTSService(config)

    print(f"\n[INFO] 可用音色:")
    for voice_id, voice_name in service.get_available_voices().items():
        print(f"  {voice_id}: {voice_name}")

    print(f"\n[INFO] 当前配置:")
    print(f"  模型: {config.model}")
    print(f"  音色: {config.voice}")
    print(f"  语速: {config.speed}")

    test_text = (
        "你好，这是流式 TTS 测试。今天天气真不错，我们一起来测试一下语音合成功能。"
    )

    print(f"\n[INFO] 测试文本: {test_text}")
    print("\n[INFO] 开始流式合成...")

    chunk_count = 0
    total_bytes = 0
    audio_data = bytearray()

    async for chunk, text_segment in service.synthesize_stream(test_text):
        chunk_count += 1
        total_bytes += len(chunk)
        audio_data.extend(chunk)
        print(
            f"  [Chunk {chunk_count}] 文本段: '{text_segment}', 音频大小: {len(chunk)} bytes"
        )

    print(f"\n[OK] 流式合成完成")
    print(f"  总块数: {chunk_count}")
    print(f"  总大小: {total_bytes} bytes")

    if audio_data:
        output_file = "voicefile/test_stream_output.pcm"
        result = await service.synthesize_to_file(test_text, output_file)
        if result.success:
            print(f"  已保存到: {output_file}")

        print("\n" + "-" * 50)
        print("尝试播放音频...")
        service.play_pcm_audio(bytes(audio_data))

    print("=" * 60)


async def test_llm_stream_tts():
    """测试 LLM 流式输出 + TTS 合成"""
    print("\n" + "=" * 60)
    print("[INFO] LLM 流式 + TTS 测试")
    print("=" * 60)

    config = TTSConfig(voice="Cherry")
    service = StreamTTSService(config)

    async def mock_llm_stream():
        """模拟 LLM 流式输出"""
        texts = [
            "你好，",
            "我是",
            "AI助手。",
            "今天",
            "天气真不错，",
            "有什么可以帮你的吗？",
        ]
        for text in texts:
            await asyncio.sleep(0.1)
            yield text

    print("\n[INFO] 模拟 LLM 流式输出 + TTS 合成...")

    chunk_count = 0
    audio_data = bytearray()

    async for chunk, text_segment in service.process_llm_stream(mock_llm_stream()):
        chunk_count += 1
        audio_data.extend(chunk)
        print(
            f"  [Chunk {chunk_count}] LLM输出: '{text_segment}', 音频: {len(chunk)} bytes"
        )

    print(f"\n[OK] 测试完成")
    print(f"  总块数: {chunk_count}")
    print(f"  总音频大小: {len(audio_data)} bytes")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_stream_tts())
    asyncio.run(test_llm_stream_tts())
