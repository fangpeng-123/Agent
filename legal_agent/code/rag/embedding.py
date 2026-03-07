"""
Embedding服务
使用BGE模型生成文本向量
"""

import os
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from ..config import Config, EmbeddingConfig


class EmbeddingService:
    """Embedding服务"""

    def __init__(self, config: Config):
        self.config = config.embedding
        self._model = None

    @property
    def model(self):
        """懒加载模型"""
        if self._model is None:
            self._model = SentenceTransformer(
                self.config.model_name, device=self.config.device
            )
        return self._model

    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """批量编码文本为向量"""
        embeddings = self.model.encode(
            texts, batch_size=batch_size, normalize_embeddings=True
        )
        return embeddings

    def encode_single(self, text: str) -> np.ndarray:
        """编码单条文本"""
        return self.encode([text])[0]

    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.model.get_sentence_embedding_dimension()

    def release(self):
        """释放模型资源"""
        if self._model:
            del self._model
            self._model = None
