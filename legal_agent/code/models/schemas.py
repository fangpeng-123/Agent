"""
数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class QueryRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")


class QueryResponse(BaseModel):
    answer: str = Field(..., description="回答内容")
    citations: List[Dict[str, Any]] = Field(default=[], description="法条引用")
    session_id: str = Field(..., description="会话ID")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"


class ServiceStatusResponse(BaseModel):
    mode: str = "auto"
    has_gpu: bool = False
    gpu_name: str = ""
    vram_gb: float = 0.0


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class HistorySession(BaseModel):
    session_id: str
    user_id: str
    messages: List[ChatMessage]
    created_at: Optional[str]
    updated_at: Optional[str]
