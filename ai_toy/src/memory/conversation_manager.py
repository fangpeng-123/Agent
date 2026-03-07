# -*- coding: utf-8 -*-
"""对话管理器"""

from typing import Dict, List, Optional
from src.memory import ChatHistoryManager, ShortTermMemory, LongTermMemory


class ConversationManager:
    """对话管理器"""

    def __init__(
        self,
        max_history: int = 20,
        short_term_ttl: int = 3600,
    ):
        self.history_manager = ChatHistoryManager()
        self.short_term_memory = ShortTermMemory(ttl_seconds=short_term_ttl)
        self.long_term_memory = LongTermMemory()
        self.max_history = max_history

    async def process_message(
        self,
        conversation_id: str,
        user_id: str,
        message: str,
        add_to_history: bool = True,
    ) -> Dict:
        """
        处理用户消息

        Returns:
            dict with context, history, etc.
        """
        if add_to_history:
            self.history_manager.add_message(conversation_id, "user", message)

        history = self.history_manager.get_history(conversation_id, self.max_history)

        short_term = self.short_term_memory.get_all()
        long_term = self.long_term_memory.load_user_profile(user_id) or {}

        return {
            "message": message,
            "history": [h.content for h in history],
            "short_term_memory": short_term,
            "long_term_memory": long_term,
        }

    async def add_response(
        self,
        conversation_id: str,
        response: str,
        metadata: Optional[Dict] = None,
    ):
        """添加助手回复"""
        self.history_manager.add_message(
            conversation_id, "assistant", response, metadata
        )

    def get_summary(self, conversation_id: str) -> str:
        """获取对话摘要"""
        history = self.history_manager.get_history(conversation_id, 10)
        return "\n".join([f"{h.role}: {h.content[:50]}..." for h in history])
