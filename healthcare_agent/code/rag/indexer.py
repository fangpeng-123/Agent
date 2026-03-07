from typing import List, Optional
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from ..config import Config
from .document_loader import DocumentLoader
from .embedding import EmbeddingService


class Indexer:
    def __init__(self, config: Config):
        self.config = config
        self.document_loader = DocumentLoader(config)
        self.embedding_service = EmbeddingService(config)
        self._index = None

    def create_index(self, documents: List, persist: bool = True) -> VectorStoreIndex:
        vector_store_config = self.config.vector_store
        chroma_config = vector_store_config.chroma

        chroma_client = chromadb.PersistentClient(path=chroma_config.get("persist_directory", "data/index/chroma"))
        collection_name = chroma_config.get("collection_name", "health_knowledge")

        collection = chroma_client.get_or_create_collection(name=collection_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)

        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        embedding_model = self.embedding_service.get_embedding_model()

        self._index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=embedding_model
        )

        if persist:
            self._index.storage_context.persist()

        return self._index

    def load_index(self) -> Optional[VectorStoreIndex]:
        vector_store_config = self.config.vector_store
        chroma_config = vector_store_config.chroma

        chroma_client = chromadb.PersistentClient(path=chroma_config.get("persist_directory", "data/index/chroma"))
        collection_name = chroma_config.get("collection_name", "health_knowledge")

        collection = chroma_client.get_collection(name=collection_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)

        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        embedding_model = self.embedding_service.get_embedding_model()

        try:
            self._index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                storage_context=storage_context,
                embed_model=embedding_model
            )
            return self._index
        except Exception as e:
            print(f"加载索引失败: {e}")
            return None

    def get_index(self) -> Optional[VectorStoreIndex]:
        if self._index is None:
            self._index = self.load_index()
        return self._index
