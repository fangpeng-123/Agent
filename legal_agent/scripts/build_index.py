#!/usr/bin/env python3
"""
构建向量索引脚本
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import load_config
from code.rag.document_loader import DocumentLoader
from code.rag.pipeline import RAGPipelineFactory
from code.services.embedding import EmbeddingService


def main():
    config = load_config()
    docs_dir = Path("data/documents")

    if not docs_dir.exists():
        print(f"目录不存在: {docs_dir}")
        return

    pdf_files = list(docs_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"未找到PDF文件: {docs_dir}")
        return

    print(f"找到 {len(pdf_files)} 个PDF文件")

    print("加载文档...")
    loader = DocumentLoader()
    documents = loader.load_directory(str(docs_dir))
    print(f"加载了 {len(documents)} 个文档块")

    print("构建索引...")
    pipeline = RAGPipelineFactory(config).create_pipeline("langchain")
    pipeline.build_index(documents)

    print("索引构建完成!")


if __name__ == "__main__":
    main()
