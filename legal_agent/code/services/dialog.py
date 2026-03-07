"""
对话管理服务
"""

import os
import sqlite3
import json
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
from ..config import Config


@dataclass
class Message:
    role: str
    content: str
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ChatSession:
    session_id: str
    user_id: str
    messages: List[Message]
    created_at: str
    updated_at: str


class DialogService:
    """对话管理服务"""

    def __init__(self, config: Config):
        self.config = config
        self.db_path = config.history.db_path
        self._ensure_db()

    def _ensure_db(self):
        """确保数据库存在"""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                messages TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def create_session(self, user_id: str) -> str:
        """创建会话"""
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        now = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?)",
            (session_id, user_id, "[]", now, now),
        )
        conn.commit()
        conn.close()

        return session_id

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        messages = json.loads(row[2])
        return ChatSession(
            session_id=row[0],
            user_id=row[1],
            messages=[Message(**m) for m in messages],
            created_at=row[3],
            updated_at=row[4],
        )

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息"""
        session = self.get_session(session_id)
        if session is None:
            return

        session.messages.append(Message(role=role, content=content))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        messages_json = json.dumps([asdict(m) for m in session.messages])
        cursor.execute(
            "UPDATE sessions SET messages = ?, updated_at = ? WHERE session_id = ?",
            (messages_json, datetime.now().isoformat(), session_id),
        )
        conn.commit()
        conn.close()

    def get_user_sessions(self, user_id: str, limit: int = 20) -> List[ChatSession]:
        """获取用户所有会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            messages = json.loads(row[2])
            sessions.append(
                ChatSession(
                    session_id=row[0],
                    user_id=row[1],
                    messages=[Message(**m) for m in messages],
                    created_at=row[3],
                    updated_at=row[4],
                )
            )
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def get_history_messages(
        self, session_id: str, max_messages: int = 10
    ) -> List[Dict]:
        """获取历史消息"""
        session = self.get_session(session_id)
        if session is None:
            return []

        messages = session.messages[-max_messages:]
        return [{"role": m.role, "content": m.content} for m in messages]
