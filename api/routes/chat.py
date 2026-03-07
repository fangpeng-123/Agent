# -*- coding: utf-8 -*-
"""聊天接口"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def chat(message: str, user_id: str = None):
    """聊天接口"""
    return {"message": "TODO: 实现聊天接口", "user_id": user_id}
