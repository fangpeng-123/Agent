from typing import Optional
from llama_index.embeddings.langchain import LangchainEmbedding
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from dashscope import get_api_key

from ..config import Config


class EmbeddingService:
    def __init__(self, config: Config):
        self.config = config
        self.mode = config.get_service_mode()
        self._embedding_model = None

    def get_embedding_model(self):
        if self._embedding_model is None:
            if self.mode == "local":
                self._embedding_model = self._create_local_embedding()
            else:
                self._embedding_model = self._create_api_embedding()
        return self._embedding_model

    def _create_local_embedding(self):
        embedding_config = self.config.embedding.local
        model_name = embedding_config.get("model_name", "BAAI/bge-small-zh")
        device = embedding_config.get("device", "cpu")

        lc_embedding = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device}
        )
        return LangchainEmbedding(lc_embedding)

    def _create_api_embedding(self):
        api_config = self.config.embedding.api
        provider = api_config.get("provider", "ali")

        if provider == "ali":
            model = api_config.get("model", "text-embedding-v2")
            lc_embedding = DashScopeEmbeddings(
                model=model,
                dashscope_api_key=get_api_key()
            )
            return LangchainEmbedding(lc_embedding)
        else:
            raise ValueError(f"不支持的Embedding提供商: {provider}")

    async def embed_text(self, text: str):
        model = self.get_embedding_model()
        return await model.aget_text_embedding(text)

    async def embed_texts(self, texts: list):
        model = self.get_embedding_model()
        return await model.aget_text_embeddings(texts)
