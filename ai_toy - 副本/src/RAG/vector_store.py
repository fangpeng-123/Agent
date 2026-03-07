# -*- coding: utf-8 -*-
"""向量存储"""

from typing import List, Optional


class VectorStore:
    """向量存储基类"""

    def __init__(self, path: str = "./model/vector_store"):
        self.path = path

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[dict]] = None,
    ):
        """添加向量"""
        pass

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        """搜索"""
        pass

    def load(self):
        """加载已存储的向量"""
        pass

    def save(self):
        """保存向量"""
        pass
