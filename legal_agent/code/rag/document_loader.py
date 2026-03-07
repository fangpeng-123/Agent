"""
文档加载器 - LangChain + LlamaIndex 集成
"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from langchain.schema import Document
from llama_index.core import Document as LIDocument
import fitz


@dataclass
class DocumentMetadata:
    filename: str
    law_name: str
    total_pages: int


class DocumentLoader:
    """文档加载器"""

    SUPPORTED_FORMATS = {".pdf"}

    LAW_NAME_MAP = {
        "宪法": "中华人民共和国宪法",
        "民法典": "中华人民共和国民法典",
        "刑法": "中华人民共和国刑法",
    }

    def load_directory(self, dir_path: str) -> List[Document]:
        """加载目录下所有文档"""
        chunks = []
        for file_path in Path(dir_path).iterdir():
            if file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                file_chunks = self.load_file(str(file_path))
                chunks.extend(file_chunks)
        return chunks

    def load_file(self, file_path: str) -> List[Document]:
        """加载单个文件"""
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return self._load_pdf(file_path)
        return []

    def _load_pdf(self, file_path: str) -> List[Document]:
        """解析PDF文件"""
        chunks = []
        law_name = self._extract_law_name(file_path)

        try:
            doc = fitz.open(file_path)
            current_chunk = ""
            current_article = ""

            for page_num, page in enumerate(doc):
                text = page.get_text()
                lines = text.split("\n")

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if self._is_article_line(line):
                        if current_chunk:
                            chunks.append(
                                self._create_doc(
                                    current_chunk,
                                    file_path,
                                    page_num + 1,
                                    law_name,
                                    current_article,
                                )
                            )
                        current_article = self._extract_article_id(line)
                        current_chunk = line
                    else:
                        if len(current_chunk) + len(line) < 500:
                            current_chunk += " " + line
                        else:
                            chunks.append(
                                self._create_doc(
                                    current_chunk,
                                    file_path,
                                    page_num + 1,
                                    law_name,
                                    current_article,
                                )
                            )
                            current_chunk = line

            if current_chunk:
                chunks.append(
                    self._create_doc(
                        current_chunk, file_path, len(doc), law_name, current_article
                    )
                )

            doc.close()
        except Exception as e:
            print(f"加载PDF失败 {file_path}: {e}")

        return chunks

    def _create_doc(
        self, text: str, source: str, page: int, law_name: str, article_id: str
    ) -> Document:
        """创建LangChain Document"""
        return Document(
            page_content=text,
            metadata={
                "source": Path(source).name,
                "page": page,
                "law_name": law_name,
                "article_id": article_id,
            },
        )

    def _extract_law_name(self, file_path: str) -> str:
        """从文件名提取法律名称"""
        filename = Path(file_path).stem
        for key, full_name in self.LAW_NAME_MAP.items():
            if key in filename:
                return full_name
        return filename

    def _is_article_line(self, line: str) -> bool:
        """判断是否为条款行"""
        import re

        pattern = r"^第[一二三四五六七八九十百千]+[条章]"
        return bool(re.match(pattern, line))

    def _extract_article_id(self, line: str) -> str:
        """提取条款ID"""
        import re

        match = re.match(r"(第[一二三四五六七八九十百千]+[条章])", line)
        return match.group(1) if match else ""

    def load_as_llama_index(self, dir_path: str) -> List[LIDocument]:
        """加载为LlamaIndex Document"""
        docs = self.load_directory(dir_path)
        return [
            LIDocument(text=doc.page_content, metadata=doc.metadata) for doc in docs
        ]

    def get_metadata(self, file_path: str) -> Optional[DocumentMetadata]:
        """获取文档元数据"""
        if Path(file_path).suffix.lower() != ".pdf":
            return None

        try:
            doc = fitz.open(file_path)
            metadata = DocumentMetadata(
                filename=Path(file_path).name,
                law_name=self._extract_law_name(file_path),
                total_pages=len(doc),
            )
            doc.close()
            return metadata
        except Exception:
            return None
