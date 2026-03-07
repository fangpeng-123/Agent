# -*- coding: utf-8 -*-
"""服务模块"""

from src.services.asr import ASRService
from src.services.tts import QwenTTSService as TTSService

__all__ = ["ASRService", "TTSService"]
