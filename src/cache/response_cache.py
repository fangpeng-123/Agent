# -*- coding: utf-8 -*-
"""响应缓存"""

import hashlib
import time
from typing import Any, Dict, Optional


class ResponseCache:
    """模型响应缓存"""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict] = {}

    def _generate_key(self, messages: str) -> str:
        """生成缓存 key"""
        return hashlib.md5(messages.encode()).hexdigest()

    def get(self, messages: str) -> Optional[str]:
        """获取缓存"""
        key = self._generate_key(messages)
        if key in self.cache:
            data = self.cache[key]
            if time.time() - data["timestamp"] < self.ttl_seconds:
                return data["result"]
            del self.cache[key]
        return None

    def set(self, messages: str, result: str):
        """设置缓存"""
        key = self._generate_key(messages)
        self.cache[key] = {
            "result": result,
            "timestamp": time.time(),
        }

    def clear(self):
        """清空缓存"""
        self.cache.clear()

    def get_stats(self) -> Dict:
        """获取缓存统计"""
        return {
            "size": len(self.cache),
            "ttl_seconds": self.ttl_seconds,
        }
