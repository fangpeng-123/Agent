# -*- coding: utf-8 -*-
"""对话历史管理模块"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path
import time


@dataclass
class ConversationMessage:
    """对话消息"""

    role: str  # user/assistant/system
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)


class ChatHistoryManager:
    """对话历史管理器"""

    def __init__(self, storage_dir: str = "./data/conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.short_term_cache: Dict[str, List[ConversationMessage]] = {}

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ):
        """添加消息"""
        message = ConversationMessage(
            role=role, content=content, metadata=metadata or {}
        )

        if conversation_id not in self.short_term_cache:
            self.short_term_cache[conversation_id] = []

        self.short_term_cache[conversation_id].append(message)

    def get_history(
        self, conversation_id: str, max_messages: int = 20
    ) -> List[ConversationMessage]:
        """获取对话历史"""
        messages = self.short_term_cache.get(conversation_id, [])
        return messages[-max_messages:]

    def clear_history(self, conversation_id: str):
        """清空对话历史"""
        if conversation_id in self.short_term_cache:
            del self.short_term_cache[conversation_id]

    def save_to_disk(self, conversation_id: str):
        """保存到磁盘"""
        messages = self.short_term_cache.get(conversation_id, [])
        if not messages:
            return

        file_path = self.storage_dir / f"conversation_{conversation_id}.json"
        data = [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
                "metadata": m.metadata,
            }
            for m in messages
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_disk(self, conversation_id: str) -> List[ConversationMessage]:
        """从磁盘加载"""
        file_path = self.storage_dir / f"conversation_{conversation_id}.json"
        if not file_path.exists():
            return []

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        return [ConversationMessage(**item) for item in data]
