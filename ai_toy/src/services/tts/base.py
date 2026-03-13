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
    MIN_SEGMENT_LENGTH = 8  # 短句合并阈值，低于此值不输出
    FAST_RESPONSE_LENGTH = 15  # 其他标点分割最小长度（保留兼容性）
    LONG_SEGMENT_LENGTH = 20  # 长句拆分阈值，超过此值进行拆分

    def __init__(self):
        self.tts_text_queue: queue.Queue[TTSMessage] = queue.Queue()
        self.tts_audio_queue: queue.Queue[TTSMessage] = queue.Queue()
        self.tts_text_buff: list[str] = []
        self.processed_chars: int = 0
        self.stop_event = threading.Event()
        self.processing_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.Lock()  # 保护 tts_text_buff 和 processed_chars

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
                            # 循环尝试分割，直到没有更多可分割的文本
                            while True:
                                segment_text = self._get_segment_text()
                                if segment_text:
                                    self._loop.run_until_complete(
                                        self._process_tts_segment(segment_text)
                                    )
                                    # 分割完成后，检查是否还有剩余文本需要处理
                                    # 如果 processed_chars 已经到达文本末尾，重置缓冲区
                                    full_text = "".join(self.tts_text_buff)
                                    if self.processed_chars >= len(full_text):
                                        self.tts_text_buff.clear()
                                        self.processed_chars = 0
                                else:
                                    # 没有更多可分割的文本，退出循环
                                    break
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
        动态文本分割 - 新策略

        分割策略：
        1. 整句保护：如果文本已经是完整句子（含句末标点）且长度≤30字，不再切分
        2. 长文本保护：如果输入文本 > 30字（来自上游缓冲区），直接返回
        3. 短句合并：当前片段 < MIN_SEGMENT_LENGTH(8字) 时，继续累积
        4. 长句拆分：当前片段 ≥ LONG_SEGMENT_LENGTH(20字) 时，在句子中间拆分

        Returns:
            分割出的文本段或 None
        """
        full_text = "".join(self.tts_text_buff)
        current_text = full_text[self.processed_chars :]

        if not current_text:
            return None

        # ========== 整句保护：如果已经是完整句子，不再二次切分 ==========
        # 条件：文本以句末标点结尾 且 长度≤30字
        if current_text[-1] in self.STRONG_PUNCTUATIONS:
            if len(current_text) <= 30:
                self.processed_chars += len(current_text)
                return current_text

        # ========== 长文本保护：来自上游缓冲区的长文本，不再切分 ==========
        # 如果是新文本块的开始，且长度 > 30 字，直接返回
        if self.processed_chars == 0 and len(current_text) > 30:
            self.processed_chars += len(current_text)
            return current_text

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

        # 没有找到任何标点
        if not candidates:
            # 检查当前文本长度，超过长句阈值需要拆分
            if len(current_text) >= self.LONG_SEGMENT_LENGTH:
                segment = self._split_long_segment(current_text)
                if segment:
                    self.processed_chars += len(segment)
                    return segment
            return None

        # 按位置排序，找最近的标点
        candidates.sort(key=lambda x: x[0])

        for pos, punct_type in candidates:
            potential_segment = current_text[: pos + 1]
            segment_len = len(potential_segment)

            if punct_type == "strong":
                # 强标点：无条件分割
                # 如果太长，进行拆分
                if segment_len >= self.LONG_SEGMENT_LENGTH:
                    segment = self._split_long_segment(potential_segment)
                    if segment:
                        self.processed_chars += len(segment)
                        return segment
                self.processed_chars += segment_len
                return potential_segment

            elif punct_type == "comma":
                # 逗号：满足最小长度才分割
                if segment_len >= self.MIN_SEGMENT_LENGTH:
                    # 如果太长，进行拆分
                    if segment_len >= self.LONG_SEGMENT_LENGTH:
                        segment = self._split_long_segment(potential_segment)
                        if segment:
                            self.processed_chars += len(segment)
                            return segment
                    self.processed_chars += segment_len
                    return potential_segment
                # 不满足最小长度，继续累积

            else:
                # 其他标点：满足最小长度才分割
                if segment_len >= self.MIN_SEGMENT_LENGTH:
                    # 如果太长，进行拆分
                    if segment_len >= self.LONG_SEGMENT_LENGTH:
                        segment = self._split_long_segment(potential_segment)
                        if segment:
                            self.processed_chars += len(segment)
                            return segment
                    self.processed_chars += segment_len
                    return potential_segment
                # 不满足最小长度，继续累积

        # 找到了标点但不满足长度条件，或者没有更多标点
        # 检查当前累积文本是否过长需要拆分
        if len(current_text) >= self.LONG_SEGMENT_LENGTH:
            segment = self._split_long_segment(current_text)
            if segment:
                self.processed_chars += len(segment)
                return segment

        return None

    def _split_long_segment(self, text: str) -> Optional[str]:
        """
        拆分长文本段

        在合适的位置（尽量保持语义完整）将长文本拆分为两部分：
        - 返回前半部分用于合成
        - 剩余部分保留在缓冲区

        Args:
            text: 待拆分的文本

        Returns:
            拆分后的前半部分文本
        """
        if len(text) < self.LONG_SEGMENT_LENGTH:
            return text

        # 优先在以下位置拆分：
        # 1. 逗号位置（保持语义相对完整）
        # 2. 顿号位置
        # 3. 空格位置（如果存在）
        # 4. 最后一个完整句子（句号、问号、感叹号之后的位置）

        # 找最后一个逗号/顿号
        split_candidates = []

        # 找逗号
        comma_pos = text.rfind("，")
        if comma_pos > 0:
            split_candidates.append(comma_pos)

        # 找顿号
        dahao_pos = text.rfind("、")
        if dahao_pos > 0:
            split_candidates.append(dahao_pos)

        # 找空格
        space_pos = text.rfind(" ")
        if space_pos > 0:
            split_candidates.append(space_pos)

        # 找最后一个句号/问号/感叹号（但不是最后一个字符）
        for punct in ("。", "？", "！"):
            pos = text.rfind(punct)
            if pos > 0 and pos < len(text) - 1:
                split_candidates.append(pos)

        # 找中间位置作为后备
        middle_pos = len(text) // 2

        if split_candidates:
            # 找最接近中间的位置
            split_candidates.sort(key=lambda x: abs(x - middle_pos))
            best_pos = split_candidates[0]

            # 返回前半部分（不包含标点）
            result = text[: best_pos + 1]
            # 将后半部分放回缓冲区
            remaining = text[best_pos + 1 :]
            if remaining:
                self.tts_text_buff = [remaining]
            return result

        # 无法找到合适的拆分点，直接从中间拆分
        split_pos = len(text) // 2
        result = text[:split_pos]
        remaining = text[split_pos:]
        if remaining:
            self.tts_text_buff = [remaining]
        return result

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
        with self._lock:
            self.tts_text_buff.clear()
            self.processed_chars = 0
        self.stop_event.clear()
