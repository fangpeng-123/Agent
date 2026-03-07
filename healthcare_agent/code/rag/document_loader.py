from typing import List, Optional
from pathlib import Path

from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.langchain import LangchainEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from langchain.embeddings import HuggingFaceEmbeddings
import chromadb

from ..config import Config


class DocumentLoader:
    def __init__(self, config: Config):
        self.config = config
        self.chunk_size = config.rag.chunk_size
        self.chunk_overlap = config.rag.chunk_overlap

    def load_documents(self, file_paths: List[str]) -> List[Document]:
        documents = []
        for file_path in file_paths:
            path = Path(file_path)
            if path.suffix.lower() == ".pdf":
                documents.extend(self._load_pdf(file_path))
            elif path.suffix.lower() == ".txt":
                documents.extend(self._load_txt(file_path))
            elif path.suffix.lower() == ".md":
                documents.extend(self._load_md(file_path))
        return documents

    def _load_pdf(self, file_path: str) -> List[Document]:
        try:
            import pymupdf
            doc = pymupdf.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return [Document(text=text, metadata={"source": file_path})]
        except Exception as e:
            print(f"加载PDF失败 {file_path}: {e}")
            return []

    def _load_txt(self, file_path: str) -> List[Document]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            return [Document(text=text, metadata={"source": file_path})]
        except Exception as e:
            print(f"加载TXT失败 {file_path}: {e}")
            return []

    def _load_md(self, file_path: str) -> List[Document]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            return [Document(text=text, metadata={"source": file_path})]
        except Exception as e:
            print(f"加载MD失败 {file_path}: {e}")
            return []

    def split_documents(self, documents: List[Document]) -> List[Document]:
        splitter = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        nodes = splitter.get_nodes_from_documents(documents)
        return nodes
