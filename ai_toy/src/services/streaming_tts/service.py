# -*- coding: utf-8 -*-
"""
Streaming TTS Service - 流式TTS服务层
封装provider，提供更高级的接口
"""

import asyncio
import time
from typing import AsyncGenerator, Optional, Callable
from dataclasses import dataclass

from .provider import StreamingTTSProvider, StreamingTTSConfig, StreamingCallback


@dataclass
class StreamingTTSResult:
    """Streaming TTS 结果"""

    audio_data: bytes = b""
    duration_ms: float = 0
    success: bool = False
    error_message: Optional[str] = None
    first_audio_delay: float = 0


def _apply_fade_out(audio_data: bytes, fade_samples: int = 480) -> bytes:
    """末尾淡出处理，防止爆音"""
    try:
        import numpy as np

        if len(audio_data) < fade_samples * 2:
            return audio_data

        data = np.frombuffer(audio_data, dtype=np.int16)
        fade_len = min(fade_samples, len(data))
        fade_curve = np.linspace(1.0, 0.0, fade_len)
        data[-fade_len:] = (data[-fade_len:] * fade_curve).astype(np.int16)
        return data.tobytes()
    except Exception:
        return audio_data


class StreamingTTSService:
    """
    流式 TTS 服务

    特点：
    - 真正的流式合成（边合成边返回）
    - 低首字延迟（<100ms）
    """

    VOICES = StreamingTTSProvider.VOICES

    def __init__(self, config: Optional[StreamingTTSConfig] = None):
        self.config = config or StreamingTTSConfig()
        self._provider: Optional[StreamingTTSProvider] = None

    def _get_provider(self) -> StreamingTTSProvider:
        """获取或创建 TTS 提供者"""
        if self._provider is None:
            self._provider = StreamingTTSProvider(self.config)
        return self._provider

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._get_provider().is_available()

    async def synthesize_stream(
        self,
        text: str,
        on_audio: Optional[Callable[[bytes, str], None]] = None,
    ) -> AsyncGenerator[tuple[bytes, str], None]:
        """
        流式合成音频 - 真正的流式：边收边yield

        Args:
            text: 要合成的文本
            on_audio: 音频回调函数（可选）

        Yields:
            (audio_data, text_segment) 元组 - 收到立即yield
        """
        if not self.is_available():
            return

        provider = self._get_provider()
        loop = asyncio.get_event_loop()

        # 用于跨线程传递音频块
        audio_queue: asyncio.Queue[Optional[bytes]] = asyncio.Queue()
        done_event = asyncio.Event()
        error_holder = [None]  # 用于跨线程传递异常

        def sync_producer():
            """同步生产者：边收音频块边放入队列"""
            start_time = time.time()
            try:
                callback = StreamingCallback()

                tts_instance = provider._create_tts_instance(callback)
                tts_instance.connect()

                audio_format = provider._get_audio_format()
                if audio_format is not None:
                    tts_instance.update_session(
                        voice=provider.config.voice,
                        response_format=audio_format,
                        mode="server_commit",
                        speed=provider.config.speed,
                    )

                # 发送文本
                tts_instance.append_text(text)
                tts_instance.finish()

                # 边收边放队列，不等全部
                while not callback.complete_event.is_set():
                    time.sleep(0.02)  # 20ms检查一次，更快响应

                    while callback.audio_chunks:
                        chunk = callback.audio_chunks.pop(0)
                        if chunk:
                            # 立即放入队列，不等待
                            try:
                                loop.call_soon_threadsafe(audio_queue.put_nowait, chunk)
                            except RuntimeError:
                                # 事件循环已关闭
                                break

                # 处理剩余音频块
                while callback.audio_chunks:
                    chunk = callback.audio_chunks.pop(0)
                    if chunk:
                        try:
                            loop.call_soon_threadsafe(audio_queue.put_nowait, chunk)
                        except RuntimeError:
                            break

            except Exception as e:
                print(f"[StreamingTTSService] 同步合成异常: {e}")
                error_holder[0] = e
            finally:
                try:
                    loop.call_soon_threadsafe(done_event.set)
                except RuntimeError:
                    pass

        # 启动后台同步任务
        producer_task = loop.run_in_executor(None, sync_producer)

        try:
            first_chunk = True
            start_time = time.time()

            # 边收边yield，不等全部
            while not done_event.is_set() or not audio_queue.empty():
                try:
                    chunk = await asyncio.wait_for(audio_queue.get(), timeout=0.1)

                    if chunk:
                        # 记录首音频延迟
                        if first_chunk:
                            first_audio_delay = (time.time() - start_time) * 1000
                            first_chunk = False
                            print(
                                f"[StreamingTTS] 首块音频到达，延迟: {first_audio_delay:.0f}ms"
                            )

                        if on_audio:
                            on_audio(chunk, text)
                        yield (chunk, text)

                except asyncio.TimeoutError:
                    # 超时继续循环，等待新音频块
                    continue

            # 等待后台任务完成
            await producer_task

            # 如果有错误，抛出
            if error_holder[0]:
                raise error_holder[0]

        except Exception as e:
            print(f"[StreamingTTSService] 流式合成异常: {e}")
            raise
        finally:
            # 确保后台任务被取消
            if not producer_task.done():
                producer_task.cancel()
                try:
                    await producer_task
                except asyncio.CancelledError:
                    pass

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
            (audio_data, text_segment) 元组
        """
        if not self.is_available():
            return

        provider = self._get_provider()

        # 确保连接已建立
        if not provider._connected:
            if not provider.connect():
                return

        text_buffer = ""

        try:
            async for text_chunk in llm_stream:
                if text_chunk:
                    text_buffer += text_chunk

                    # 遇句末标点或缓冲区过长时触发合成
                    should_flush = (text_buffer and text_buffer[-1] in "。！？") or len(
                        text_buffer
                    ) >= 30

                    if should_flush and text_buffer.strip():
                        # 执行合成
                        async for audio_data in self.synthesize_stream(
                            text_buffer, on_audio
                        ):
                            yield audio_data
                        text_buffer = ""

            # 处理剩余文本
            if text_buffer.strip():
                async for audio_data in self.synthesize_stream(text_buffer, on_audio):
                    yield audio_data

        finally:
            provider.disconnect()

    async def synthesize(self, text: str) -> StreamingTTSResult:
        """
        合成完整音频

        Args:
            text: 要合成的文本

        Returns:
            StreamingTTSResult
        """
        start_time = time.time()
        audio_data = bytearray()
        first_audio_delay = 0

        chunk_idx = 0
        async for chunk, _ in self.synthesize_stream(text):
            audio_data.extend(chunk)
            chunk_idx += 1
            if first_audio_delay == 0:
                first_audio_delay = (time.time() - start_time) * 1000
            print(f"[StreamingTTS] 收到音频块 {chunk_idx}: {len(chunk)} bytes")

        result = StreamingTTSResult(
            audio_data=_apply_fade_out(bytes(audio_data)),
            duration_ms=(time.time() - start_time) * 1000,
            success=len(audio_data) > 0,
            first_audio_delay=first_audio_delay,
        )

        if not result.success:
            result.error_message = "音频数据为空"

        return result

    async def synthesize_to_file(self, text: str, file_path: str) -> StreamingTTSResult:
        """合成音频并保存到文件"""
        import os

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
        """获取可用音色"""
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

            format_map = {
                8: pyaudio.paUInt8,
                16: pyaudio.paInt16,
                32: pyaudio.paInt32,
            }
            audio_format = format_map.get(bits_per_sample, pyaudio.paInt16)

            p = pyaudio.PyAudio()
            stream = p.open(
                format=audio_format,
                channels=channels,
                rate=sample_rate,
                output=True,
            )
            print("[StreamingTTS] 正在播放音频...")
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("[StreamingTTS] 播放完成")
            return True
        except ImportError:
            print("[StreamingWARN] 未安装 pyaudio")
            return False
        except Exception as e:
            print(f"[StreamingTTS] 播放失败: {e}")
            return False
