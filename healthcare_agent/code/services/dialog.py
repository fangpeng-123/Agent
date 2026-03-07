from typing import List, Optional
from datetime import datetime
import sqlite3
from pathlib import Path

from ..config import Config
from ..models.schemas import DialogSession, Message


class DialogService:
    def __init__(self, config: Config):
        self.config = config
        self.history_config = config.history
        self.db_path = self.history_config.db_path
        self.max_sessions = self.history_config.max_sessions
        self._init_db()

    def _init_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        conn.commit()
        conn.close()

    def create_session(self, user_id: str) -> str:
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO sessions (session_id, user_id) VALUES (?, ?)",
            (session_id, user_id)
        )

        self._cleanup_old_sessions(cursor, user_id)

        conn.commit()
        conn.close()

        return session_id

    def get_or_create_session(self, user_id: str) -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT session_id FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
            (user_id,)
        )
        result = cursor.fetchone()

        if result:
            session_id = result[0]
            cursor.execute(
                "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (session_id,)
            )
        else:
            session_id = self.create_session(user_id)

        conn.commit()
        conn.close()

        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )

        cursor.execute(
            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,)
        )

        conn.commit()
        conn.close()

    def get_history_messages(self, session_id: str, limit: Optional[int] = None) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC"
        params = (session_id,)

        if limit:
            cursor.execute(f"{query} LIMIT ?", (*params, limit))
        else:
            cursor.execute(query, params)

        results = cursor.fetchall()
        conn.close()

        messages = [{"role": row[0], "content": row[1]} for row in results]
        return messages

    def get_user_sessions(self, user_id: str) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT session_id, created_at, updated_at FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        )
        results = cursor.fetchall()
        conn.close()

        sessions = [
            {
                "session_id": row[0],
                "created_at": row[1],
                "updated_at": row[2]
            }
            for row in results
        ]
        return sessions

    def delete_session(self, session_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def _cleanup_old_sessions(self, cursor, user_id: str):
        cursor.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id = ?",
            (user_id,)
        )
        count = cursor.fetchone()[0]

        if count > self.max_sessions:
            cursor.execute(
                f"""
                DELETE FROM sessions WHERE session_id IN (
                    SELECT session_id FROM sessions WHERE user_id = ?
                    ORDER BY updated_at ASC LIMIT ?
                )
                """,
                (user_id, count - self.max_sessions)
            )
