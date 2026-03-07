import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import yaml
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ServiceConfig:
    mode: str = "auto"
    local_model_path: str = "./models"


@dataclass
class EmbeddingConfig:
    local: dict
    api: dict


@dataclass
class LLMConfig:
    local: dict
    api: dict


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
class VectorStoreConfig:
    type: str = "chroma"
    chroma: dict


@dataclass
class HistoryConfig:
    db_path: str = "data/sqlite/history.db"
    max_sessions: int = 100


@dataclass
class SafetyConfig:
    enabled: bool = True
    sensitive_words: list = None


@dataclass
class WeChatWorkConfig:
    corp_id: str
    agent_id: str
    secret: str
    token: str
    encoding_aes_key: str
    callback_url: str
    api_base_url: str
    safe_mode: int
    enable_id_trans: int


@dataclass
class ReviewConfig:
    enabled: bool = True
    customer_service_user_id: str = ""
    levels: dict = None


@dataclass
class ReportConfig:
    max_file_size: int = 10485760
    allowed_formats: list = None
    ocr_enabled: bool = True
    ocr_engine: str = "paddleocr"
    storage_path: str = "data/reports"


@dataclass
class NotificationConfig:
    enabled: bool = True
    auto_remind: bool = True
    reminder_times: list = None


@dataclass
class MembershipConfig:
    enabled: bool = True
    levels: dict = None


@dataclass
class Config:
    service: ServiceConfig
    embedding: EmbeddingConfig
    llm: LLMConfig
    rag: RAGConfig
    server: ServerConfig
    vector_store: VectorStoreConfig
    history: HistoryConfig
    safety: SafetyConfig
    wechat_work: WeChatWorkConfig
    review: ReviewConfig
    report: ReportConfig
    notification: NotificationConfig
    membership: MembershipConfig

    def get_service_mode(self) -> str:
        if self.service.mode == "auto":
            use_local = os.getenv("USE_LOCAL_MODEL", "auto").lower()
            if use_local == "local":
                return "local"
            elif use_local == "api":
                return "api"
            else:
                return "api"
        return self.service.mode


class HardwareDetector:
    def __init__(self):
        self.has_gpu = False
        self.gpu_name = None
        self.vram_gb = 0
        self._detect()

    def _detect(self):
        try:
            import torch
            self.has_gpu = torch.cuda.is_available()
            if self.has_gpu:
                self.gpu_name = torch.cuda.get_device_name(0)
                self.vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        except ImportError:
            pass

    def check(self) -> "HardwareStatus":
        return HardwareStatus(
            has_gpu=self.has_gpu,
            gpu_name=self.gpu_name,
            vram_gb=self.vram_gb
        )


@dataclass
class HardwareStatus:
    has_gpu: bool
    gpu_name: Optional[str]
    vram_gb: float


def load_config(config_path: str = "config.yaml") -> Config:
    config_dir = Path(__file__).parent.parent
    config_file = config_dir / config_path

    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")

    with open(config_file, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    def get_nested(data, *keys, default=None):
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return default
        return data

    return Config(
        service=ServiceConfig(**config_data.get("service", {})),
        embedding=EmbeddingConfig(
            local=config_data.get("embedding", {}).get("local", {}),
            api=config_data.get("embedding", {}).get("api", {})
        ),
        llm=LLMConfig(
            local=config_data.get("llm", {}).get("local", {}),
            api=config_data.get("llm", {}).get("api", {})
        ),
        rag=RAGConfig(**config_data.get("rag", {})),
        server=ServerConfig(**config_data.get("server", {})),
        vector_store=VectorStoreConfig(
            type=config_data.get("vector_store", {}).get("type", "chroma"),
            chroma=config_data.get("vector_store", {}).get("chroma", {})
        ),
        history=HistoryConfig(**config_data.get("history", {})),
        safety=SafetyConfig(
            enabled=config_data.get("safety", {}).get("enabled", True),
            sensitive_words=config_data.get("safety", {}).get("sensitive_words", [])
        ),
        wechat_work=WeChatWorkConfig(
            corp_id=os.getenv("WECHAT_WORK_CORP_ID", config_data.get("wechat_work", {}).get("corp_id", "")),
            agent_id=os.getenv("WECHAT_WORK_AGENT_ID", config_data.get("wechat_work", {}).get("agent_id", "")),
            secret=os.getenv("WECHAT_WORK_SECRET", config_data.get("wechat_work", {}).get("secret", "")),
            token=os.getenv("WECHAT_WORK_TOKEN", config_data.get("wechat_work", {}).get("token", "")),
            encoding_aes_key=os.getenv("WECHAT_WORK_ENCODING_AES_KEY", config_data.get("wechat_work", {}).get("encoding_aes_key", "")),
            callback_url=os.getenv("WECHAT_WORK_CALLBACK_URL", config_data.get("wechat_work", {}).get("callback_url", "")),
            api_base_url=config_data.get("wechat_work", {}).get("api_base_url", "https://qyapi.weixin.qq.com"),
            safe_mode=config_data.get("wechat_work", {}).get("safe_mode", 1),
            enable_id_trans=config_data.get("wechat_work", {}).get("enable_id_trans", 0)
        ),
        review=ReviewConfig(
            enabled=config_data.get("review", {}).get("enabled", True),
            customer_service_user_id=os.getenv("CUSTOMER_SERVICE_USER_ID", config_data.get("review", {}).get("customer_service_user_id", "")),
            levels=config_data.get("review", {}).get("levels", {})
        ),
        report=ReportConfig(
            max_file_size=config_data.get("report", {}).get("max_file_size", 10485760),
            allowed_formats=config_data.get("report", {}).get("allowed_formats", ["pdf"]),
            ocr_enabled=config_data.get("report", {}).get("ocr_enabled", True),
            ocr_engine=config_data.get("report", {}).get("ocr_engine", "paddleocr"),
            storage_path=config_data.get("report", {}).get("storage_path", "data/reports")
        ),
        notification=NotificationConfig(
            enabled=config_data.get("notification", {}).get("enabled", True),
            auto_remind=config_data.get("notification", {}).get("auto_remind", True),
            reminder_times=config_data.get("notification", {}).get("reminder_times", ["09:00", "18:00"])
        ),
        membership=MembershipConfig(
            enabled=config_data.get("membership", {}).get("enabled", True),
            levels=config_data.get("membership", {}).get("levels", {})
        )
    )
