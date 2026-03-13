# -*- coding: utf-8 -*-
"""
Streaming TTS 模块
真正的流式语音合成服务
"""

from .provider import StreamingTTSProvider
from .service import StreamingTTSService, StreamingTTSConfig

__all__ = [
    "StreamingTTSProvider",
    "StreamingTTSService",
    "StreamingTTSConfig",
]
