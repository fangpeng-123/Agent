"""
向量索引管理 - 支持Milvus/FAISS
"""

from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain_community.vectorstores import Milvus, FAISS
from ..config import Config


class VectorIndexer:
    """向量索引管理器"""

    def __init__(self, config: Config):
        self.config = config
        self._vectorstore = None

    @property
    def vectorstore(self):
        return self._vectorstore

    def create_milvus_index(self, documents: List[Document], embedding):
        """创建Milvus索引"""
        self._vectorstore = Milvus.from_documents(
            documents=documents,
            embedding=embedding,
            connection_args={
                "host": self.config.milvus.host,
                "port": self.config.milvus.port,
            },
            collection_name="legal_docs",
        )
        return self._vectorstore

    def create_faiss_index(
        self, documents: List[Document], embedding, save_path: str = "data/index"
    ):
        """创建FAISS索引（本地备选）"""
        import os

        os.makedirs(save_path, exist_ok=True)

        self._vectorstore = FAISS.from_documents(
            documents=documents, embedding=embedding
        )

        self._vectorstore.save_local(save_path)
        return self._vectorstore

    def load_faiss_index(self, embedding, load_path: str = "data/index"):
        """加载本地FAISS索引"""
        self._vectorstore = FAISS.load_local(
            load_path, embedding, allow_dangerous_deserialization=True
        )
        return self._vectorstore

    def search(self, query: str, embedding, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索"""
        if self._vectorstore is None:
            raise Exception("索引未创建")

        results = self._vectorstore.similarity_search_with_score(query, k=top_k)

        hits = []
        for doc, score in results:
            hits.append(
                {
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", ""),
                    "page": doc.metadata.get("page", 0),
                    "law_name": doc.metadata.get("law_name", ""),
                    "article_id": doc.metadata.get("article_id", ""),
                    "score": float(score),
                }
            )

        return hits

    def as_retriever(self, **kwargs):
        """转换为Retriever"""
        if self._vectorstore is None:
            raise Exception("索引未创建")
        return self._vectorstore.as_retriever(**kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self._vectorstore is None:
            return {"num_documents": 0}

        try:
            if hasattr(self._vectorstore, "index"):
                return {"num_documents": self._vectorstore.index.ntotal}
            return {"num_documents": len(self._vectorstore.docstore._dict)}
        except Exception:
            return {"num_documents": 0}

    def delete_collection(self):
        """删除集合"""
        if self._vectorstore:
            try:
                from pymilvus import utility

                utility.drop_collection("legal_docs")
            except Exception:
                pass
            self._vectorstore = None
