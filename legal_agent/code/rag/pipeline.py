"""
RAG Pipeline - LangChain + LlamaIndex 集成
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Milvus, FAISS
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import CompactRefine
from ..config import Config
from ..services.embedding import EmbeddingService
from ..services.llm import LLMService


@dataclass
class RetrievalResult:
    text: str
    source: str
    page: int
    law_name: str
    article_id: str
    score: float = 0.0


@dataclass
class RAGResponse:
    answer: str
    citations: List[Dict[str, Any]]
    sources: List[RetrievalResult]


class LangChainRAGPipeline:
    """LangChain RAG Pipeline"""

    SYSTEM_PROMPT = """你是一个法律知识助手，根据提供的法律条文回答用户问题。

要求：
1. 只基于提供的法条内容回答，不要编造
2. 回答要清晰、有条理，适当使用列表
3. 必须附带具体的法条原文引用
4. 语言通俗易懂，非专业人士也能理解

每次回答后请添加免责声明：【本回答仅供参考，不构成法律意见，涉及具体法律问题请咨询专业律师】"""

    def __init__(self, config: Config):
        self.config = config
        self.embedding_service = EmbeddingService(config)
        self.llm_service = LLMService(config)
        self.vectorstore = None
        self.qa_chain = None

    def build_index(self, documents: List[Document]):
        """构建向量索引"""
        self.vectorstore = Milvus.from_documents(
            documents=documents,
            embedding=self.embedding_service.as_langchain_embeddings(),
            connection_args={
                "host": self.config.milvus.host,
                "port": self.config.milvus.port,
            },
            collection_name="legal_docs",
        )

        self._build_qa_chain()

    def _build_qa_chain(self):
        """构建QA链"""
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": self.config.rag.top_k}
        )

        prompt_template = """基于以下参考法条回答用户问题。如果参考内容中没有相关信息，请明确说明。

## 参考法条
{context}

## 用户问题
{question}

请回答用户问题，并注明法条来源。"""

        prompt = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm_service.get_langchain_llm(),
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
        )

    def query(self, question: str, history: List[Dict] = None) -> RAGResponse:
        """查询"""
        if self.qa_chain is None:
            raise Exception("索引未构建，请先调用build_index")

        history_text = ""
        if history:
            for h in history[-5:]:
                role = "用户" if h["role"] == "user" else "助手"
                history_text += f"{role}: {h['content']}\n"

        full_question = (
            f"## 对话历史\n{history_text}\n## 用户问题\n{question}"
            if history_text
            else question
        )

        result = self.qa_chain.invoke({"query": full_question})

        docs = result.get("source_documents", [])
        citations = self._extract_citations(docs)

        return RAGResponse(
            answer=result["result"],
            citations=citations,
            sources=[self._doc_to_result(d) for d in docs],
        )

    def _extract_citations(self, docs: List[Document]) -> List[Dict[str, Any]]:
        """提取引用"""
        citations = []
        seen = set()

        for doc in docs:
            metadata = doc.metadata or {}
            key = f"{metadata.get('law_name', '')}_{metadata.get('article_id', '')}"
            if key not in seen:
                seen.add(key)
                citations.append(
                    {
                        "law": metadata.get("law_name", ""),
                        "article": metadata.get("article_id", ""),
                        "source": metadata.get("source", ""),
                        "page": metadata.get("page", 0),
                    }
                )

        return citations

    def _doc_to_result(self, doc: Document) -> RetrievalResult:
        """Document转RetrievalResult"""
        metadata = doc.metadata or {}
        return RetrievalResult(
            text=doc.page_content[:500],
            source=metadata.get("source", ""),
            page=metadata.get("page", 0),
            law_name=metadata.get("law_name", ""),
            article_id=metadata.get("article_id", ""),
        )


class LlamaIndexRAGPipeline:
    """LlamaIndex RAG Pipeline"""

    def __init__(self, config: Config):
        self.config = config
        self.embedding_service = EmbeddingService(config)
        self.llm_service = LLMService(config)
        self.index = None
        self.query_engine = None

    def build_index(self, documents: List[Document]):
        """构建索引"""
        from llama_index.core import Document as LIDocument

        li_docs = [
            LIDocument(text=doc.page_content, metadata=doc.metadata)
            for doc in documents
        ]

        Settings.embed_model = self.embedding_service.as_langchain_embeddings()

        self.index = VectorStoreIndex.from_documents(
            li_docs,
            splitter=SentenceSplitter(
                chunk_size=self.config.rag.chunk_size,
                chunk_overlap=self.config.rag.chunk_overlap,
            ),
        )

        self.query_engine = self.index.as_query_engine(
            similarity_top_k=self.config.rag.top_k, response_synthesizer=CompactRefine()
        )

    def query(self, question: str, history: List[Dict] = None) -> RAGResponse:
        """查询"""
        if self.query_engine is None:
            raise Exception("索引未构建")

        full_question = question
        if history:
            history_text = "\n".join(
                [f"{h['role']}: {h['content']}" for h in history[-5:]]
            )
            full_question = f"历史对话:\n{history_text}\n\n当前问题: {question}"

        response = self.query_engine.query(full_question)

        sources = []
        citations = []

        for node in response.source_nodes:
            metadata = node.metadata or {}
            result = RetrievalResult(
                text=node.text[:500],
                source=metadata.get("source", ""),
                page=metadata.get("page", 0),
                law_name=metadata.get("law_name", ""),
                article_id=metadata.get("article_id", ""),
            )
            sources.append(result)

            key = f"{result.law_name}_{result.article_id}"
            if key not in [
                c.get("law", "") + "_" + c.get("article", "") for c in citations
            ]:
                citations.append(
                    {
                        "law": result.law_name,
                        "article": result.article_id,
                        "source": result.source,
                        "page": result.page,
                    }
                )

        return RAGResponse(answer=str(response), citations=citations, sources=sources)


class RAGPipelineFactory:
    """RAG Pipeline工厂"""

    def __init__(self, config: Config):
        self.config = config

    def create_pipeline(self, framework: str = "langchain") -> LangChainRAGPipeline:
        """创建Pipeline"""
        if framework == "llamaindex":
            return LlamaIndexRAGPipeline(self.config)
        return LangChainRAGPipeline(self.config)
