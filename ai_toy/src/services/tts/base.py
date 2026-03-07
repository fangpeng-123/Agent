# -*- coding: utf-8 -*-
"""
TTS 提供者基类
实现双队列缓冲机制和智能文本分割
"""

import queue
import threading
import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Any, AsyncGenerator


class ContentType(Enum):
    """消息内容类型"""

    TEXT = "text"
    AUDIO = "audio"
    ERROR = "error"
    END = "end"


@dataclass
class TTSMessage:
    """TTS 消息"""

    content_type: ContentType
    content: Any = None
    text: str = ""
    audio_data: bytes = b""
    error: Optional[str] = None


class TTSProviderBase(ABC):
    """
    TTS 提供者基类

    实现双队列缓冲机制：
    - tts_text_queue: 文本输入队列
    - tts_audio_queue: 音频输出队列

    实现动态文本分割：
    - 根据已累积文本长度动态选择分割标点
    - 短文本（<5字）：只用强标点，避免首字切断
    - 中等长度（5-15字）：逗号 + 强标点，快速首响
    - 长文本（>15字）：任意标点，保持流畅
    """

    # 动态分割标点集合
    STRONG_PUNCTUATIONS = ("。", "？", "！", "；", "…")
    MEDIUM_PUNCTUATIONS = ("，", ",", "。", "？", "！", "；", "…")
    ALL_PUNCTUATIONS = ("，", ",", "。", "？", "！", "；", "、", "…", "：", ":")

    # 动态分割阈值
    MIN_SEGMENT_LENGTH = 8  # 逗号分割最小长度，避免过短分割
    FAST_RESPONSE_LENGTH = 15  # 其他标点分割最小长度

    def __init__(self):
        self.tts_text_queue: queue.Queue[TTSMessage] = queue.Queue()
        self.tts_audio_queue: queue.Queue[TTSMessage] = queue.Queue()
        self.tts_text_buff: list[str] = []
        self.processed_chars: int = 0
        self.stop_event = threading.Event()
        self.processing_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self):
        """启动文本处理线程"""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.stop_event.clear()
            self.processing_thread = threading.Thread(
                target=self._text_processing_thread, daemon=True
            )
            self.processing_thread.start()

    def stop(self):
        """停止处理"""
        self.stop_event.set()
        self.tts_text_queue.put(TTSMessage(content_type=ContentType.END))
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)

    def put_text(self, text: str):
        """
        放入文本到队列

        Args:
            text: 文本内容
        """
        if text:
            self.tts_text_queue.put(
                TTSMessage(content_type=ContentType.TEXT, content=text)
            )

    def finish_text(self):
        """标记文本输入结束"""
        self.tts_text_queue.put(TTSMessage(content_type=ContentType.END))

    def get_audio(self, timeout: float = 30.0) -> Optional[TTSMessage]:
        """
        从队列获取音频

        Args:
            timeout: 超时时间（秒）

        Returns:
            TTSMessage 或 None（超时）
        """
        try:
            return self.tts_audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _text_processing_thread(self):
        """
        文本处理线程

        从文本队列获取消息，累积文本直到遇到标点，
        然后调用 TTS API 合成音频，放入音频队列
        """
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            while not self.stop_event.is_set():
                try:
                    message = self.tts_text_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                if message.content_type == ContentType.END:
                    self._process_remaining_text()
                    self.tts_audio_queue.put(TTSMessage(content_type=ContentType.END))
                    break

                if message.content_type == ContentType.TEXT:
                    text = message.content
                    if text:
                        filtered_text = self._filter_text(text)
                        if filtered_text:
                            self.tts_text_buff.append(filtered_text)
                            segment_text = self._get_segment_text()
                            if segment_text:
                                self._loop.run_until_complete(
                                    self._process_tts_segment(segment_text)
                                )
        except Exception as e:
            self.tts_audio_queue.put(
                TTSMessage(content_type=ContentType.ERROR, error=str(e))
            )
        finally:
            if self._loop:
                self._loop.close()

    def _filter_text(self, text: str) -> str:
        """
        过滤文本中的特殊字符

        Args:
            text: 原始文本

        Returns:
            过滤后的文本
        """
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("\r\n", " ").replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _get_segment_text(self) -> Optional[str]:
        """
        动态文本分割

        分割策略：
        - 强标点（句号等）：无条件分割，保证语义完整
        - 逗号：分割后长度 >= MIN_SEGMENT_LENGTH 才分割
        - 其他标点：分割后长度 >= FAST_RESPONSE_LENGTH 才分割

        Returns:
            分割出的文本段或 None
        """
        full_text = "".join(self.tts_text_buff)
        current_text = full_text[self.processed_chars :]

        if not current_text:
            return None

        # 找到所有标点位置
        strong_pos = self._find_first_punctuation(
            current_text, self.STRONG_PUNCTUATIONS
        )
        comma_pos = self._find_first_punctuation(current_text, ("，", ","))
        other_puncts = tuple(
            p
            for p in self.ALL_PUNCTUATIONS
            if p not in self.STRONG_PUNCTUATIONS and p not in ("，", ",")
        )
        other_pos = self._find_first_punctuation(current_text, other_puncts)

        # 构建候选分割点列表：(位置, 类型)
        candidates = []
        if strong_pos != -1:
            candidates.append((strong_pos, "strong"))
        if comma_pos != -1:
            candidates.append((comma_pos, "comma"))
        if other_pos != -1:
            candidates.append((other_pos, "other"))

        # 按位置排序，找最近的标点
        candidates.sort(key=lambda x: x[0])

        for pos, punct_type in candidates:
            potential_segment = current_text[: pos + 1]
            segment_len = len(potential_segment)

            if punct_type == "strong":
                # 强标点：无条件分割
                self.processed_chars += segment_len
                return potential_segment
            elif punct_type == "comma":
                # 逗号：满足最小长度才分割
                if segment_len >= self.MIN_SEGMENT_LENGTH:
                    self.processed_chars += segment_len
                    return potential_segment
            else:
                # 其他标点：满足快速响应长度才分割
                if segment_len >= self.FAST_RESPONSE_LENGTH:
                    self.processed_chars += segment_len
                    return potential_segment

        return None

        segment = None

        # 1. 优先在强标点（句号等）处分割
        strong_pos = self._find_first_punctuation(
            current_text, self.STRONG_PUNCTUATIONS
        )
        if strong_pos != -1:
            segment = current_text[: strong_pos + 1]
            self.processed_chars += len(segment)
            return segment

        # 2. 检查逗号位置，满足最小长度才分割
        comma_pos = self._find_first_punctuation(current_text, ("，", ","))
        if comma_pos != -1:
            potential_segment = current_text[: comma_pos + 1]
            if len(potential_segment) >= self.MIN_SEGMENT_LENGTH:
                segment = potential_segment
                self.processed_chars += len(segment)
                return segment

        # 3. 检查其他标点位置，满足快速响应长度才分割
        other_puncts = tuple(
            p
            for p in self.ALL_PUNCTUATIONS
            if p not in self.STRONG_PUNCTUATIONS and p not in ("，", ",")
        )
        other_pos = self._find_first_punctuation(current_text, other_puncts)
        if other_pos != -1:
            potential_segment = current_text[: other_pos + 1]
            if len(potential_segment) >= self.FAST_RESPONSE_LENGTH:
                segment = potential_segment
                self.processed_chars += len(segment)
                return segment

        return None

        # 先尝试在强标点处分割
        strong_pos = self._find_first_punctuation(
            current_text, self.STRONG_PUNCTUATIONS
        )
        medium_pos = self._find_first_punctuation(
            current_text, self.MEDIUM_PUNCTUATIONS
        )
        all_pos = self._find_first_punctuation(current_text, self.ALL_PUNCTUATIONS)

        segment = None

        # 优先使用强标点（句号等），保证语义完整
        if strong_pos != -1:
            segment = current_text[: strong_pos + 1]
        # 中等长度（5-15字）可以用逗号分割
        elif medium_pos != -1:
            potential_segment = current_text[: medium_pos + 1]
            if len(potential_segment) >= self.MIN_SEGMENT_LENGTH:
                segment = potential_segment
        # 长文本（>15字）可以在任意标点分割
        elif all_pos != -1:
            potential_segment = current_text[: all_pos + 1]
            if len(potential_segment) >= self.FAST_RESPONSE_LENGTH:
                segment = potential_segment

        if segment:
            self.processed_chars += len(segment)
            return segment

        return None

    def _find_first_punctuation(self, text: str, punctuations: tuple) -> int:
        """
        查找第一个标点符号位置

        Args:
            text: 文本
            punctuations: 标点符号元组

        Returns:
            标点位置，未找到返回 -1
        """
        for i, char in enumerate(text):
            if char in punctuations:
                return i
        return -1

    def _process_remaining_text(self):
        """处理剩余的未合成文本"""
        full_text = "".join(self.tts_text_buff)
        remaining_text = full_text[self.processed_chars :].strip()

        if remaining_text:
            assert self._loop is not None
            self._loop.run_until_complete(self._process_tts_segment(remaining_text))

    async def _process_tts_segment(self, text: str):
        """
        处理一个文本段的 TTS 合成

        Args:
            text: 文本段
        """
        try:
            audio_generator = self._stream_tts_impl(text)
            async for audio_chunk in audio_generator:
                if audio_chunk:
                    self.tts_audio_queue.put(
                        TTSMessage(
                            content_type=ContentType.AUDIO,
                            audio_data=audio_chunk,
                            text=text,
                        )
                    )
        except Exception as e:
            self.tts_audio_queue.put(
                TTSMessage(
                    content_type=ContentType.ERROR,
                    error=f"TTS 合成失败: {str(e)}",
                    text=text,
                )
            )

    @abstractmethod
    async def _stream_tts_impl(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        流式 TTS 实现的抽象方法

        Args:
            text: 要合成的文本

        Yields:
            音频数据块（bytes）
        """
        if False:
            yield b""

    def reset(self):
        """重置状态"""
        self.tts_text_buff.clear()
        self.processed_chars = 0
        self.stop_event.clear()
