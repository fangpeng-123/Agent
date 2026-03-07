# -*- coding: utf-8 -*-
"""缓存策略管理器"""

from src.cache.intent_cache import IntentCache
from src.cache.rag_cache import RAGCache
from src.cache.response_cache import ResponseCache


class CacheManager:
    """缓存管理器"""

    def __init__(
        self,
        intent_ttl: int = 300,
        rag_ttl: int = 3600,
        response_ttl: int = 300,
    ):
        self.intent_cache = IntentCache(ttl_seconds=intent_ttl)
        self.rag_cache = RAGCache(ttl_seconds=rag_ttl)
        self.response_cache = ResponseCache(ttl_seconds=response_ttl)

    def get_intent(self, text: str):
        """获取意图缓存"""
        return self.intent_cache.get(text)

    def set_intent(self, text: str, result):
        """设置意图缓存"""
        self.intent_cache.set(text, result)

    def get_rag(self, query: str, user_id: str = None):
        """获取 RAG 缓存"""
        return self.rag_cache.get(query, user_id)

    def set_rag(self, query: str, result, user_id: str = None):
        """设置 RAG 缓存"""
        self.rag_cache.set(query, result, user_id)

    def get_response(self, messages: str):
        """获取响应缓存"""
        return self.response_cache.get(messages)

    def set_response(self, messages: str, result: str):
        """设置响应缓存"""
        self.response_cache.set(messages, result)

    def clear_all(self):
        """清空所有缓存"""
        self.intent_cache.clear()
        self.rag_cache.clear()
        self.response_cache.clear()

    def get_all_stats(self) -> dict:
        """获取所有缓存统计"""
        return {
            "intent": self.intent_cache.get_stats(),
            "rag": {},
            "response": self.response_cache.get_stats(),
        }
