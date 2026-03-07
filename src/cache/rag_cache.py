# -*- coding: utf-8 -*-
"""RAG 检索缓存"""

import hashlib
import time
from typing import Any, Dict, List, Optional


class RAGCache:
    """RAG 检索结果缓存"""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict] = {}

    def _generate_key(self, query: str, user_id: str = None) -> str:
        """生成缓存 key"""
        content = f"{query}:{user_id}" if user_id else query
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, query: str, user_id: str = None) -> Optional[List[Dict]]:
        """获取缓存"""
        key = self._generate_key(query, user_id)
        if key in self.cache:
            data = self.cache[key]
            if time.time() - data["timestamp"] < self.ttl_seconds:
                return data["result"]
            del self.cache[key]
        return None

    def set(self, query: str, result: List[Dict], user_id: str = None):
        """设置缓存"""
        key = self._generate_key(query, user_id)
        self.cache[key] = {
            "result": result,
            "timestamp": time.time(),
        }

    def clear(self):
        """清空缓存"""
        self.cache.clear()
