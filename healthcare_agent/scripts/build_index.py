import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from code.config import load_config
from code.rag.document_loader import DocumentLoader
from code.rag.indexer import Indexer


def build_index():
    config = load_config()

    loader = DocumentLoader(config)

    documents = loader.load_documents([
        "data/knowledge/health_guide.pdf",
        "data/knowledge/medical_standards.pdf",
        "data/knowledge/diet_advice.md",
    ])

    nodes = loader.split_documents(documents)

    indexer = Indexer(config)
    indexer.create_index(nodes, persist=True)

    print("索引构建完成!")


if __name__ == "__main__":
    build_index()
