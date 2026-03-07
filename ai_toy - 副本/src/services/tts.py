# -*- coding: utf-8 -*-
"""通义千问 TTS 语音合成服务"""

import os
import time
import base64
import asyncio
import aiohttp
from dataclasses import dataclass
from typing import Optional, AsyncGenerator
from dotenv import load_dotenv

try:
    import dashscope
    from dashscope import MultiModalConversation

    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False

load_dotenv()


@dataclass
class TTSConfig:
    """TTS 配置"""

    api_key: str = ""
    model: str = "qwen3-tts-flash"
    voice: str = "Cherry"
    language_type: str = "Chinese"
    speed: float = 1.0
    volume: float = 1.0
    format: str = "wav"


@dataclass
class TTSResult:
    """TTS 结果"""

    audio_data: bytes
    duration_ms: float
    success: bool
    error_message: Optional[str] = None


class QwenTTSService:
    """通义千问 TTS 服务"""

    VOICES = {
        "Cherry": "女声-客服",
        "Xi": "男声-新闻",
        "Yaqi": "男声-故事",
        "Aiya": "女声-直播",
        "Xiaoxian": "女声-儿童",
        "Ethan": "男声-教育",
        "Liam": "男声-专业",
        "NPU": "女声-标准",
        "Xiaochen": "女声-新闻",
        "Xiaomao": "女声-活泼",
    }

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self.config.api_key = self.config.api_key or os.getenv("DASHSCOPE_API_KEY", "")

        if DASHSCOPE_AVAILABLE:
            dashscope.api_key = self.config.api_key

    def is_available(self) -> bool:
        """检查服务是否可用"""
        if not DASHSCOPE_AVAILABLE:
            return False
        if not self.config.api_key:
            return False
        return True

    async def _download_audio(self, url: str) -> bytes:
        """下载音频文件"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    return b""
        except Exception:
            return b""

    async def synthesize(self, text: str) -> TTSResult:
        """同步合成语音"""
        if not self.is_available():
            return TTSResult(
                audio_data=b"",
                duration_ms=0,
                success=False,
                error_message="DashScope SDK 未安装或未设置 DASHSCOPE_API_KEY",
            )

        start_time = time.time()

        try:
            response = MultiModalConversation.call(
                model=self.config.model,
                text=text,
                voice=self.config.voice,
                language_type=self.config.language_type,
                stream=False,
            )

            if isinstance(response, dict):
                status_code = response.get("status_code", response.get("code", 200))
                if status_code == 200:
                    output = response.get("output", {})
                    audio_info = output.get("audio", {})

                    audio_data = b""
                    if isinstance(audio_info, dict):
                        audio_url = audio_info.get("url", "")
                        audio_base64 = audio_info.get("data", "")

                        if audio_url:
                            audio_data = await self._download_audio(audio_url)
                        elif audio_base64 and isinstance(audio_base64, str):
                            audio_data = base64.b64decode(audio_base64)
                    elif isinstance(audio_info, str):
                        audio_data = base64.b64decode(audio_info)

                    duration_ms = (time.time() - start_time) * 1000
                    return TTSResult(
                        audio_data=audio_data, duration_ms=duration_ms, success=True
                    )
                else:
                    message = response.get("message", response.get("error", "未知错误"))
                    return TTSResult(
                        audio_data=b"",
                        duration_ms=(time.time() - start_time) * 1000,
                        success=False,
                        error_message=f"API 错误 ({status_code}): {message}",
                    )
            else:
                return TTSResult(
                    audio_data=b"",
                    duration_ms=(time.time() - start_time) * 1000,
                    success=False,
                    error_message=f"未知响应格式: {type(response)}",
                )

        except Exception as e:
            return TTSResult(
                audio_data=b"",
                duration_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=f"请求异常: {str(e)}",
            )

    async def synthesize_to_file(self, text: str, file_path: str) -> TTSResult:
        """合成语音并保存到文件"""
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
        """获取可用的音色列表"""
        return self.VOICES


async def test_qwen_tts():
    """测试通义千问 TTS 服务"""
    config = TTSConfig(
        api_key=os.getenv("DASHSCOPE_API_KEY", ""),
        model="qwen3-tts-flash",
        voice="Cherry",
        language_type="Chinese",
    )

    tts_service = QwenTTSService(config)

    print("\n" + "=" * 60)
    print("[INFO] 通义千问 TTS 服务测试")
    print("=" * 60)

    print(f"\n[INFO] 可用音色:")
    for voice_id, voice_name in tts_service.get_available_voices().items():
        print(f"  {voice_id}: {voice_name}")

    test_text = "你好，这是通义千问 TTS 语音合成测试。"

    result = await tts_service.synthesize(test_text)

    if result.success:
        print(f"\n[OK] TTS 合成成功")
        print(f"  音频大小: {len(result.audio_data)} bytes")
        print(f"  耗时: {result.duration_ms:.2f} ms")

        output_file = "voicefile/test_output.wav"
        file_result = await tts_service.synthesize_to_file(test_text, output_file)
        if file_result.success:
            print(f"  已保存到: {output_file}")
    else:
        print(f"\n[ERROR] TTS 合成失败: {result.error_message}")

    print("=" * 60)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_qwen_tts())
