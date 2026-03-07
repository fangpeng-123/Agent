# -*- coding: utf-8 -*-
"""对话历史接口"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path

router = APIRouter()

CONVERSATION_DIR = Path("./data/conversations")


class ConversationRequest(BaseModel):
    """对话请求"""

    conversation_id: str
    user_id: str


class MessageRequest(BaseModel):
    """消息请求"""

    conversation_id: str
    role: str  # user/assistant
    content: str


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """获取对话历史"""
    file_path = CONVERSATION_DIR / f"conversation_{conversation_id}.json"
    if not file_path.exists():
        return {"messages": []}

    with open(file_path, encoding="utf-8") as f:
        return {"messages": json.load(f)}


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除对话"""
    file_path = CONVERSATION_DIR / f"conversation_{conversation_id}.json"
    if file_path.exists():
        file_path.unlink()
    return {"success": True}
