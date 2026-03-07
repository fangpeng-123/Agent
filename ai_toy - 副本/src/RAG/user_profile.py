# -*- coding: utf-8 -*-
"""用户画像检索"""

from typing import List, Optional

from src.RAG.embeddings import Embeddings
from src.RAG.vector_store import VectorStore


class UserProfileRAG:
    """用户画像 RAG"""

    def __init__(
        self,
        embeddings_model: Embeddings = None,
        vector_store: VectorStore = None,
    ):
        self.embeddings = embeddings_model or Embeddings()
        self.vector_store = vector_store or VectorStore()

    def add_user_profile(
        self, user_id: str, profile: str, metadata: Optional[dict] = None
    ):
        """添加用户画像"""
        embedding = self.embeddings.embed_text(profile)
        self.vector_store.add(
            texts=[profile],
            embeddings=[embedding],
            metadata=[{"user_id": user_id, **(metadata or {})}],
        )

    def search_user_profile(
        self, query: str, user_id: str = None, top_k: int = 3
    ) -> List[dict]:
        """搜索用户画像"""
        query_embedding = self.embeddings.embed_text(query)
        results = self.vector_store.search(query_embedding, top_k=top_k)
        if user_id:
            results = [
                r for r in results if r.get("metadata", {}).get("user_id") == user_id
            ]
        return results

    def retrieve_context(self, query: str, user_id: str = None) -> str:
        """检索上下文"""
        results = self.search_user_profile(query, user_id)
        return "\n".join([r["text"] for r in results])
