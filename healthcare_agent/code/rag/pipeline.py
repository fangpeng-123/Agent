from typing import List, Optional
from dataclasses import dataclass

from llama_index.core import VectorStoreIndex

from ..config import Config
from .indexer import Indexer


@dataclass
class QueryResult:
    answer: str
    sources: List[str]


class RAGPipeline:
    def __init__(self, config: Config, index: VectorStoreIndex):
        self.config = config
        self.index = index
        self.top_k = config.rag.top_k

    def query(self, question: str, history: Optional[List] = None) -> QueryResult:
        query_engine = self.index.as_query_engine(
            similarity_top_k=self.top_k,
            response_mode="compact"
        )

        response = query_engine.query(question)

        sources = []
        if hasattr(response, "source_nodes"):
            for node in response.source_nodes:
                if hasattr(node, "metadata") and "source" in node.metadata:
                    sources.append(node.metadata["source"])

        return QueryResult(
            answer=str(response),
            sources=sources
        )


class RAGPipelineFactory:
    def __init__(self, config: Config):
        self.config = config

    def create_pipeline(self, index: Optional[VectorStoreIndex] = None) -> RAGPipeline:
        if index is None:
            indexer = Indexer(self.config)
            index = indexer.get_index()
            if index is None:
                raise ValueError("索引不存在，请先创建索引")

        return RAGPipeline(self.config, index)
