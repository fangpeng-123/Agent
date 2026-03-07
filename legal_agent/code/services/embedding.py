"""
Embedding服务 - LangChain集成
支持本地模型和阿里云API
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from langchain.embeddings.base import Embeddings
from langchain.embeddings import HuggingFaceEmbeddings
import httpx
from ..config import Config


class BaseEmbeddingService(ABC):
    """Embedding服务基类"""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass


class LocalEmbeddingService(BaseEmbeddingService):
    """本地Embedding服务"""

    def __init__(self, config: Config):
        self.config = config.embedding["local"]
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = HuggingFaceEmbeddings(
                model_name=self.config.model_name,
                model_kwargs={"device": self.config.device},
            )
        return self._model

    def embed_query(self, text: str) -> List[float]:
        return self.model.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.embed_documents(texts)

    def embed_documents_with_batch(
        self, texts: List[str], batch_size: int = 32
    ) -> List[List[float]]:
        """批量嵌入"""
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self.model.embed_documents(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings

    def get_dimension(self) -> int:
        return self.model.client.get_sentence_embedding_dimension()


class AliEmbeddingService(BaseEmbeddingService):
    """阿里云Embedding API服务"""

    API_URL = (
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-embedding/generation"
    )

    def __init__(self, config: Config):
        self.config = config.embedding["api"]
        self.api_key = config.dashscope_api_key
        self.client = httpx.AsyncClient(timeout=120.0)

    async def _call_api(
        self, texts: List[str], is_query: bool = False
    ) -> List[List[float]]:
        """调用API"""
        input_texts = [t[:1000] for t in texts]

        payload = {
            "model": self.config.model,
            "input": {"texts": input_texts},
            "parameters": {"dimension": self.config.dimensions if is_query else 512},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = await self.client.post(self.API_URL, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        embeddings = result.get("output", {}).get("embeddings", [])
        return [e["embedding"] for e in embeddings]

    async def embed_query(self, text: str) -> List[float]:
        embeddings = await self._call_api([text], is_query=True)
        return embeddings[0]

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return await self._call_api(texts, is_query=False)

    async def close(self):
        await self.client.aclose()


class EmbeddingService:
    """Embedding服务工厂"""

    def __init__(self, config: Config):
        self.config = config
        self._local_service: Optional[LocalEmbeddingService] = None
        self._api_service: Optional[AliEmbeddingService] = None

    def get_service(self) -> BaseEmbeddingService:
        """获取合适的服务"""
        if self.config.is_local_mode():
            if self._local_service is None:
                self._local_service = LocalEmbeddingService(self.config)
            return self._local_service
        else:
            if self._api_service is None:
                self._api_service = AliEmbeddingService(self.config)
            return self._api_service

    def as_langchain_embeddings(self) -> Embeddings:
        """转换为LangChain Embeddings"""
        if self.config.is_local_mode():
            return self._local_service.model
        else:
            return AliLangChainEmbeddings(self._api_service)


class AliLangChainEmbeddings(Embeddings):
    """阿里云Embedding的LangChain包装器"""

    def __init__(self, service: AliEmbeddingService):
        self.service = service

    def embed_query(self, text: str) -> List[float]:
        import asyncio

        return asyncio.get_event_loop().run_until_complete(
            self.service.embed_query(text)
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        import asyncio

        return asyncio.get_event_loop().run_until_complete(
            self.service.embed_documents(texts)
        )
