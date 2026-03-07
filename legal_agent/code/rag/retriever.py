"""
向量检索器
负责检索相关法律条款
"""

from typing import List, Optional
from dataclasses import dataclass, field
import numpy as np
from ..config import Config
from .embedding import EmbeddingService
from .indexer import Indexer
from .text_splitter import TextChunk


@dataclass
class RetrievalResult:
    """检索结果"""

    text: str = ""
    source: str = ""
    page: int = 0
    law_name: str = ""
    article_id: str = ""
    score: float = 0.0


class Retriever:
    """向量检索器"""

    def __init__(self, config: Config):
        self.config = config
        self.embedding = EmbeddingService(config)
        self.indexer = Indexer(config)

    def retrieve(
        self, query: str, top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """检索相关文档"""
        if top_k is None:
            top_k = self.config.rag.top_k

        query_vector = self.embedding.encode_single(query)
        hits = self.indexer.search(query_vector, top_k)

        results = []
        for hit in hits:
            results.append(
                RetrievalResult(
                    text=hit["text"],
                    source=hit["source"],
                    page=hit["page"],
                    law_name=hit["law_name"],
                    article_id=hit["article_id"],
                    score=hit["score"],
                )
            )

        return results

    def retrieve_with_filter(
        self, query: str, law_name: str = None, top_k: int = 5
    ) -> List[RetrievalResult]:
        """带筛选条件的检索"""
        results = self.retrieve(query, top_k * 2)

        if law_name:
            results = [r for r in results if law_name in r.law_name]
            results = results[:top_k]

        return results

    def rerank(
        self, query: str, candidates: List[RetrievalResult], top_k: int = 3
    ) -> List[RetrievalResult]:
        """重排序（简化版：按原始分数排序）"""
        sorted_candidates = sorted(candidates, key=lambda x: x.score, reverse=True)
        return sorted_candidates[:top_k]

    def build_context(self, results: List[RetrievalResult]) -> str:
        """构建检索上下文"""
        contexts = []
        for r in results:
            citation = (
                f"【{r.law_name} {r.article_id}】"
                if r.article_id
                else f"【{r.source}】"
            )
            contexts.append(f"{citation}\n{r.text}")

        return "\n\n".join(contexts)

    def get_citations(self, results: List[RetrievalResult]) -> List[dict]:
        """提取引用信息"""
        citations = []
        seen = set()

        for r in results:
            key = f"{r.law_name}_{r.article_id}"
            if key not in seen:
                seen.add(key)
                citations.append(
                    {
                        "law": r.law_name,
                        "article": r.article_id,
                        "source": r.source,
                        "page": r.page,
                        "score": r.score,
                    }
                )

        return citations
