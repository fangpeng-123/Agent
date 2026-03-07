"""
文本分块器
按条款将法律文档分块
"""

import re
from typing import List
from dataclasses import dataclass
from .document_loader import DocumentChunk


@dataclass
class TextChunk:
    """文本块"""

    text: str
    source: str
    page: int
    law_name: str
    article_id: str = ""


class TextSplitter:
    """文本分块器"""

    ARTICLE_PATTERN = re.compile(r"(第[一二三四五六七八九十百千]+[条章])")

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: List[DocumentChunk]) -> List[TextChunk]:
        """分割文档列表"""
        chunks = []
        for doc in documents:
            doc_chunks = self.split_document(doc)
            chunks.extend(doc_chunks)
        return chunks

    def split_document(self, document: DocumentChunk) -> List[TextChunk]:
        """分割单个文档"""
        text = document.text
        lines = text.split("\n")
        chunks = []
        current_chunk = ""
        current_article = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            article_match = self.ARTICLE_PATTERN.match(line)
            if article_match:
                if current_chunk:
                    chunks.append(
                        self._create_chunk(document, current_chunk, current_article)
                    )
                current_article = article_match.group(1)
                current_chunk = line
            else:
                if len(current_chunk) + len(line) < self.chunk_size:
                    current_chunk += " " + line
                else:
                    chunks.append(
                        self._create_chunk(document, current_chunk, current_article)
                    )
                    current_chunk = line

        if current_chunk:
            chunks.append(self._create_chunk(document, current_chunk, current_article))

        return chunks

    def _create_chunk(
        self, document: DocumentChunk, text: str, article_id: str
    ) -> TextChunk:
        """创建文本块"""
        return TextChunk(
            text=text.strip(),
            source=document.source,
            page=document.page,
            law_name=document.law_name,
            article_id=article_id,
        )

    def split_by_paragraph(self, text: str) -> List[str]:
        """按段落分割"""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return paragraphs

    def split_by_sentence(self, text: str) -> List[str]:
        """按句子分割"""
        sentences = re.split(r"[。！？]", text)
        return [s.strip() + "。" for s in sentences if s.strip()]
