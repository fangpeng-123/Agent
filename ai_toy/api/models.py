# -*- coding: utf-8 -*-
"""Pydantic 数据模型"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求"""

    message: str
    user_id: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    """聊天响应"""

    content: str
    intent: str
    tool_calls: List[Dict[str, Any]] = []
    metrics: Optional[Dict[str, Any]] = None


class ToolCallRequest(BaseModel):
    """工具调用请求"""

    tool_name: str
    arguments: Dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    """工具调用响应"""

    tool_name: str
    result: str
    duration_ms: float


class WeatherRequest(BaseModel):
    """天气请求"""

    city: str


class WeatherResponse(BaseModel):
    """天气响应"""

    city: str
    weather: str
    temperature: float
    humidity: int
