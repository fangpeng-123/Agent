# -*- coding: utf-8 -*-
"""API 路由"""

from fastapi import APIRouter

router = APIRouter()

from api.routes import chat, weather, tools, health, conversation, user_profile

router.include_router(chat.router, prefix="/chat", tags=["聊天"])
router.include_router(weather.router, prefix="/weather", tags=["天气"])
router.include_router(tools.router, prefix="/tools", tags=["工具"])
router.include_router(health.router, prefix="/health", tags=["健康检查"])
router.include_router(conversation.router, prefix="/conversations", tags=["对话历史"])
router.include_router(user_profile.router, prefix="/users", tags=["用户画像"])
