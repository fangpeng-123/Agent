# -*- coding: utf-8 -*-
"""嵌入模型"""

from typing import List


class Embeddings:
    """嵌入模型基类"""

    def __init__(self, model_path: str = "./model/embeddings"):
        self.model_path = model_path

    def embed_text(self, text: str) -> List[float]:
        """单文本嵌入"""
        pass

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量文本嵌入"""
        pass
