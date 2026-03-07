from typing import Optional
from ..config import Config


class EmbeddingService:
    def __init__(self, config: Config):
        self.config = config
        self.mode = config.get_service_mode()
        self._init_embedding()

    def _init_embedding(self):
        if self.mode == "api":
            self._init_api_embedding()
        else:
            self._init_local_embedding()

    def _init_api_embedding(self):
        provider = self.config.embedding.api.provider
        if provider == "ali":
            self._init_ali_embedding()
        elif provider == "openai":
            self._init_openai_embedding()

    def _init_ali_embedding(self):
        import dashscope
        from dashscope import TextEmbedding

        dashscope.api_key = self._get_api_key("DASHSCOPE_API_KEY")
        self.embedding_client = TextEmbedding
        self.model = self.config.embedding.api.model

    def _init_openai_embedding(self):
        from openai import OpenAI

        api_key = self._get_api_key("OPENAI_API_KEY")
        self.embedding_client = OpenAI(api_key=api_key)
        self.model = self.config.embedding.api.model

    def _init_local_embedding(self):
        from sentence_transformers import SentenceTransformer

        model_path = self.config.embedding.local.model_name
        device = self.config.embedding.local.device

        self.model = SentenceTransformer(model_path, device=device)

    def _get_api_key(self, env_var: str) -> str:
        import os
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"请设置环境变量 {env_var}")
        return api_key

    async def embed(self, text: str) -> list:
        if self.mode == "api":
            return await self._embed_api(text)
        else:
            return await self._embed_local(text)

    async def _embed_api(self, text: str) -> list:
        provider = self.config.embedding.api.provider
        if provider == "ali":
            return await self._embed_ali(text)
        elif provider == "openai":
            return await self._embed_openai(text)

    async def _embed_ali(self, text: str) -> list:
        response = self.embedding_client.call(
            model=self.model,
            input=text
        )
        return response.output["embeddings"][0]["embedding"]

    async def _embed_openai(self, text: str) -> list:
        response = self.embedding_client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    async def _embed_local(self, text: str) -> list:
        embedding = self.model.encode(text)
        return embedding.tolist()

    async def embed_batch(self, texts: list) -> list:
        if self.mode == "api":
            embeddings = []
            for text in texts:
                embedding = await self.embed(text)
                embeddings.append(embedding)
            return embeddings
        else:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
