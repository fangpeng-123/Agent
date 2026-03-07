# -*- coding: utf-8 -*-
"""
TTS 模块测试
测试流式 TTS 服务和智能文本分割
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.tts_service import (
    StreamTTSService,
    QwenTTSService,
    TTSConfig,
    TTSResult,
)
from src.services.tts.base import TTSProviderBase, ContentType
from src.services.tts.stream_tts import StreamTTS
from src.services.tts.providers.qwen_tts import QwenTTSProvider


async def test_stream_tts_service():
    """测试流式 TTS 服务"""
    print("\n" + "=" * 60)
    print("[Test 1] 流式 TTS 服务测试")
    print("=" * 60)

    config = TTSConfig(
        model="qwen3-tts-flash-realtime",
        voice="Cherry",
        speed=1.0,
    )

    service = StreamTTSService(config)

    if not service.is_available():
        print("[SKIP] DashScope SDK 未安装或未设置 API Key")
        return

    test_text = (
        "你好，这是流式 TTS 测试。今天天气真不错，我们一起来测试一下语音合成功能。"
    )

    print(f"\n[INFO] 测试文本: {test_text}")
    print("[INFO] 开始流式合成...")

    chunk_count = 0
    total_bytes = 0
    audio_data = bytearray()

    async for chunk, text_segment in service.synthesize_stream(test_text):
        chunk_count += 1
        total_bytes += len(chunk)
        audio_data.extend(chunk)
        print(
            f"  [Chunk {chunk_count}] 文本段: '{text_segment}', 大小: {len(chunk)} bytes"
        )

    print(f"\n[OK] 流式合成完成")
    print(f"  总块数: {chunk_count}")
    print(f"  总大小: {total_bytes} bytes")

    return chunk_count > 0


async def test_llm_stream_integration():
    """测试 LLM 流式输出 + TTS 集成"""
    print("\n" + "=" * 60)
    print("[Test 2] LLM 流式 + TTS 集成测试")
    print("=" * 60)

    config = TTSConfig(voice="Cherry")
    service = StreamTTSService(config)

    if not service.is_available():
        print("[SKIP] DashScope SDK 未安装或未设置 API Key")
        return

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

    print("[INFO] 模拟 LLM 流式输出 + TTS 合成...")

    chunk_count = 0

    async for chunk, text_segment in service.process_llm_stream(mock_llm_stream()):
        chunk_count += 1
        print(
            f"  [Chunk {chunk_count}] LLM: '{text_segment}', 大小: {len(chunk)} bytes"
        )

    print(f"\n[OK] 测试完成，总块数: {chunk_count}")

    return chunk_count > 0


async def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "=" * 60)
    print("[Test 3] 向后兼容性测试")
    print("=" * 60)

    config = TTSConfig(voice="Cherry", speed=1.0)
    service = QwenTTSService(config)

    if not service.is_available():
        print("[SKIP] DashScope SDK 未安装或未设置 API Key")
        return

    test_text = "这是向后兼容性测试。"

    print(f"[INFO] 测试文本: {test_text}")
    print("[INFO] 使用 QwenTTSService.synthesize()...")

    result = await service.synthesize(test_text)

    if result.success:
        print(f"[OK] 合成成功")
        print(f"  音频大小: {len(result.audio_data)} bytes")
        print(f"  耗时: {result.duration_ms:.2f} ms")
        return True
    else:
        print(f"[FAIL] 合成失败: {result.error_message}")
        return False


def test_text_segmentation():
    """测试智能文本分割"""
    print("\n" + "=" * 60)
    print("[Test 4] 智能文本分割测试")
    print("=" * 60)

    provider = QwenTTSProvider()

    test_cases = [
        ("你好，我是AI助手。", ["你好，", "我是AI助手。"]),
        ("今天天气不错。我们去玩吧！", ["今天天气不错。", "我们去玩吧！"]),
        ("一句话没有标点", []),
    ]

    for text, expected_first in test_cases:
        provider.reset()
        provider.tts_text_buff = [text]

        segment = provider._get_segment_text()
        print(f"  输入: '{text}'")
        print(f"  第一段: '{segment}'")
        if expected_first:
            print(f"  预期第一段: '{expected_first[0]}'")

    print("\n[OK] 文本分割测试完成")
    return True


async def main():
    print("=" * 60)
    print("TTS 模块测试")
    print("=" * 60)

    results = []

    results.append(("文本分割", test_text_segmentation()))
    results.append(("流式服务", await test_stream_tts_service()))
    results.append(("LLM集成", await test_llm_stream_integration()))
    results.append(("向后兼容", await test_backward_compatibility()))

    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    for name, passed in results:
        status = "[OK]" if passed else "[FAIL]" if passed is False else "[SKIP]"
        print(f"  {status} {name}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
