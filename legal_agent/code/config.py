"""
配置管理 + 硬件检测模块
"""

import os
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import yaml


@dataclass
class LocalEmbeddingConfig:
    model_name: str = "BAAI/bge-small-zh"
    device: str = "cpu"


@dataclass
class LocalLLMConfig:
    model_name: str = "Qwen/Qwen2.5-7B-Instruct"
    device: str = "cpu"


@dataclass
class APIEmbeddingConfig:
    provider: str = "ali"
    model: str = "text-embedding-v2"
    dimensions: int = 1536


@dataclass
class APILLMConfig:
    provider: str = "ali"
    model: str = "qwen-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7


@dataclass
class ServiceConfig:
    mode: str = "auto"
    local_model_path: str = "./models"


@dataclass
class RAGConfig:
    top_k: int = 5
    max_history: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 100


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass
class MilvusConfig:
    host: str = "localhost"
    port: int = 19530


@dataclass
class HistoryConfig:
    db_path: str = "data/sqlite/history.db"


@dataclass
class SafetyConfig:
    enabled: bool = True
    sensitive_words: list = field(default_factory=list)


@dataclass
class HardwareStatus:
    has_gpu: bool = False
    gpu_name: str = ""
    vram_gb: float = 0.0
    recommended_mode: str = "api"


class HardwareDetector:
    """硬件检测器"""

    def __init__(self):
        self._gpu_info = None

    def check(self) -> HardwareStatus:
        """检测硬件状态"""
        has_gpu, gpu_name, vram_gb = self._detect_gpu()

        status = HardwareStatus(
            has_gpu=has_gpu,
            gpu_name=gpu_name,
            vram_gb=vram_gb,
            recommended_mode=self._recommend_mode(has_gpu, vram_gb),
        )
        return status

    def _detect_gpu(self) -> tuple:
        """检测GPU信息"""
        try:
            import torch

            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                if device_count > 0:
                    gpu_name = torch.cuda.get_device_name(0)
                    vram_gb = torch.cuda.get_device_properties(0).total_memory / (
                        1024**3
                    )
                    return True, gpu_name, round(vram_gb, 1)
        except Exception:
            pass
        return False, "", 0.0

    def _recommend_mode(self, has_gpu: bool, vram_gb: float) -> str:
        """推荐服务模式"""
        if has_gpu and vram_gb >= 4.0:
            return "local"
        return "api"

    def select_service_mode(self) -> str:
        """选择服务模式"""
        mode = os.getenv("USE_LOCAL_MODEL", "auto").lower()

        if mode in ["local", "api"]:
            return mode

        status = self.check()
        return status.recommended_mode


class Config:
    """配置类"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.hardware_detector = HardwareDetector()

        self.service = self._load_service_config()
        self.embedding = self._load_embedding_config()
        self.llm = self._load_llm_config()
        self.rag = self._load_rag_config()
        self.server = self._load_server_config()
        self.milvus = self._load_milvus_config()
        self.history = self._load_history_config()
        self.safety = self._load_safety_config()

        self.feishu_app_id = os.getenv("FEISHU_APP_ID", "")
        self.feishu_app_secret = os.getenv("FEISHU_APP_SECRET", "")
        self.feishu_verify_token = os.getenv("FEISHU_VERIFY_TOKEN", "")
        self.feishu_encrypt_key = os.getenv("FEISHU_ENCRYPT_KEY", "")
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")

    def _load_service_config(self) -> ServiceConfig:
        """加载服务配置"""
        data = self._load_yaml()
        service_data = data.get("service", {})
        return ServiceConfig(
            mode=service_data.get("mode", "auto"),
            local_model_path=service_data.get("local_model_path", "./models"),
        )

    def _load_embedding_config(self) -> dict:
        """加载Embedding配置"""
        data = self._load_yaml()
        embedding_data = data.get("embedding", {})
        return {
            "local": LocalEmbeddingConfig(
                model_name=os.getenv(
                    "LOCAL_EMBEDDING_MODEL",
                    embedding_data.get("local", {}).get(
                        "model_name", "BAAI/bge-small-zh"
                    ),
                ),
                device=os.getenv(
                    "LOCAL_DEVICE", embedding_data.get("local", {}).get("device", "cpu")
                ),
            ),
            "api": APIEmbeddingConfig(
                provider=embedding_data.get("api", {}).get("provider", "ali"),
                model=embedding_data.get("api", {}).get("model", "text-embedding-v2"),
            ),
        }

    def _load_llm_config(self) -> dict:
        """加载LLM配置"""
        data = self._load_yaml()
        llm_data = data.get("llm", {})
        return {
            "local": LocalLLMConfig(
                model_name=os.getenv(
                    "LOCAL_LLM_MODEL",
                    llm_data.get("local", {}).get(
                        "model_name", "Qwen/Qwen2.5-7B-Instruct"
                    ),
                ),
                device=os.getenv(
                    "LOCAL_DEVICE", llm_data.get("local", {}).get("device", "cpu")
                ),
            ),
            "api": APILLMConfig(
                provider=llm_data.get("api", {}).get("provider", "ali"),
                model=llm_data.get("api", {}).get("model", "qwen-turbo"),
                max_tokens=llm_data.get("api", {}).get("max_tokens", 2000),
                temperature=llm_data.get("api", {}).get("temperature", 0.7),
            ),
        }

    def _load_rag_config(self) -> RAGConfig:
        """加载RAG配置"""
        data = self._load_yaml()
        rag_data = data.get("rag", {})
        return RAGConfig(
            top_k=rag_data.get("top_k", 5),
            max_history=rag_data.get("max_history", 5),
            chunk_size=rag_data.get("chunk_size", 500),
            chunk_overlap=rag_data.get("chunk_overlap", 100),
        )

    def _load_server_config(self) -> ServerConfig:
        """加载服务器配置"""
        data = self._load_yaml()
        server_data = data.get("server", {})
        return ServerConfig(
            host=server_data.get("host", "0.0.0.0"), port=server_data.get("port", 8000)
        )

    def _load_milvus_config(self) -> MilvusConfig:
        """加载Milvus配置"""
        data = self._load_yaml()
        milvus_data = data.get("vector_store", {}).get("milvus", {})
        return MilvusConfig(
            host=os.getenv("MILVUS_HOST", milvus_data.get("host", "localhost")),
            port=int(os.getenv("MILVUS_PORT", milvus_data.get("port", 19530))),
        )

    def _load_history_config(self) -> HistoryConfig:
        """加载历史配置"""
        data = self._load_yaml()
        history_data = data.get("history", {})
        return HistoryConfig(
            db_path=history_data.get("db_path", "data/sqlite/history.db")
        )

    def _load_safety_config(self) -> SafetyConfig:
        """加载安全配置"""
        data = self._load_yaml()
        safety_data = data.get("safety", {})
        default_words = ["分裂", "叛乱", "颠覆", "恐怖", "色情", "毒品"]
        words = safety_data.get("sensitive_words", default_words)
        return SafetyConfig(
            enabled=safety_data.get("enabled", True), sensitive_words=words
        )

    def _load_yaml(self) -> dict:
        """加载YAML配置"""
        if not self.config_path.exists():
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_service_mode(self) -> str:
        """获取服务模式"""
        mode = self.service.mode
        if mode == "auto":
            return self.hardware_detector.select_service_mode()
        return mode

    def is_local_mode(self) -> bool:
        """是否使用本地模式"""
        return self.get_service_mode() == "local"

    def is_api_mode(self) -> bool:
        """是否使用API模式"""
        return self.get_service_mode() == "api"


def load_config(config_path: str = "config.yaml") -> Config:
    """加载配置"""
    return Config(config_path)
