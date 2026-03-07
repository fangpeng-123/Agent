# -*- coding: utf-8 -*-
"""短期记忆模块"""

from typing import Dict, List, Optional
from collections import OrderedDict
import time


class ShortTermMemory:
    """短期记忆管理器"""

    def __init__(self, max_items: int = 100, ttl_seconds: int = 3600):
        """
        Args:
            max_items: 最大记忆条目数
            ttl_seconds: 记忆过期时间（秒）
        """
        self.max_items = max_items
        self.ttl_seconds = ttl_seconds
        self.memory: OrderedDict[str, Dict] = OrderedDict()

    def add(self, key: str, value: any, metadata: Optional[Dict] = None):
        """添加记忆"""
        self._clean_expired()

        self.memory[key] = {
            "value": value,
            "metadata": metadata or {},
            "created_at": time.time(),
            "accessed_at": time.time(),
        }

        if len(self.memory) > self.max_items:
            self.memory.popitem(last=False)

    def get(self, key: str) -> any:
        """获取记忆"""
        if key not in self.memory:
            return None

        item = self.memory[key]
        if self._is_expired(item):
            del self.memory[key]
            return None

        item["accessed_at"] = time.time()
        return item["value"]

    def _is_expired(self, item: Dict) -> bool:
        """检查是否过期"""
        return time.time() - item["created_at"] > self.ttl_seconds

    def _clean_expired(self):
        """清理过期记忆"""
        expired_keys = [k for k, v in self.memory.items() if self._is_expired(v)]
        for k in expired_keys:
            del self.memory[k]

    def clear(self):
        """清空所有记忆"""
        self.memory.clear()

    def get_all(self) -> Dict[str, any]:
        """获取所有有效记忆"""
        self._clean_expired()
        return {k: v["value"] for k, v in self.memory.items()}
