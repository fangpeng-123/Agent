# -*- coding: utf-8 -*-
"""ASR 语音识别服务（预留）"""


class ASRService:
    """语音识别服务"""

    def __init__(self, model_path: str = "./model/asr"):
        self.model_path = model_path

    async def recognize(self, audio_data: bytes) -> str:
        """语音转文字"""
        raise NotImplementedError("ASR 服务尚未实现")

    async def recognize_from_file(self, file_path: str) -> str:
        """从文件识别"""
        raise NotImplementedError("ASR 服务尚未实现")

    async def stream_recognize(self, audio_stream):
        """流式识别"""
        raise NotImplementedError("ASR 服务尚未实现")
