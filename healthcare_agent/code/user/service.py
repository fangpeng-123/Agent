from typing import Optional, List
from datetime import datetime
import sqlite3
from pathlib import Path
import json

from ..config import Config
from ..models.schemas import User, HealthProfile, MembershipLevel


class UserService:
    def __init__(self, config: Config):
        self.config = config
        self.db_path = "data/sqlite/users.db"
        self._init_db()

    def _init_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                membership_level TEXT DEFAULT 'trial',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_profiles (
                user_id TEXT PRIMARY KEY,
                basic_info TEXT,
                medical_history TEXT,
                lifestyle TEXT,
                indicators TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        conn.commit()
        conn.close()

    def create_user(self, user_id: str, name: Optional[str] = None, membership_level: MembershipLevel = MembershipLevel.TRIAL) -> User:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, name, membership_level) VALUES (?, ?, ?)",
            (user_id, name, membership_level.value)
        )

        conn.commit()
        conn.close()

        return self.get_user(user_id)

    def get_user(self, user_id: str) -> Optional[User]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_id, name, membership_level, created_at, updated_at FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return User(
                user_id=result[0],
                name=result[1],
                membership_level=MembershipLevel(result[2]),
                created_at=datetime.fromisoformat(result[3]),
                updated_at=datetime.fromisoformat(result[4])
            )
        return None

    def get_or_create_user(self, user_id: str) -> User:
        user = self.get_user(user_id)
        if user is None:
            user = self.create_user(user_id)
        return user

    def update_user_name(self, user_id: str, name: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (name, user_id)
        )

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def update_membership_level(self, user_id: str, membership_level: MembershipLevel) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET membership_level = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (membership_level.value, user_id)
        )

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def get_health_profile(self, user_id: str) -> Optional[HealthProfile]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_id, basic_info, medical_history, lifestyle, indicators, created_at, updated_at FROM health_profiles WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return HealthProfile(
                user_id=result[0],
                basic_info=json.loads(result[1]) if result[1] else {},
                medical_history=json.loads(result[2]) if result[2] else {},
                lifestyle=json.loads(result[3]) if result[3] else {},
                indicators=json.loads(result[4]) if result[4] else [],
                created_at=datetime.fromisoformat(result[5]),
                updated_at=datetime.fromisoformat(result[6])
            )
        return None

    def update_health_profile(self, user_id: str, profile: HealthProfile) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO health_profiles
            (user_id, basic_info, medical_history, lifestyle, indicators, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                user_id,
                json.dumps(profile.basic_info.model_dump()) if hasattr(profile.basic_info, 'model_dump') else json.dumps(profile.basic_info),
                json.dumps(profile.medical_history.model_dump()) if hasattr(profile.medical_history, 'model_dump') else json.dumps(profile.medical_history),
                json.dumps(profile.lifestyle.model_dump()) if hasattr(profile.lifestyle, 'model_dump') else json.dumps(profile.lifestyle),
                json.dumps([ind.model_dump() if hasattr(ind, 'model_dump') else ind for ind in profile.indicators])
            )
        )

        conn.commit()
        conn.close()

        return True

    def get_all_users(self) -> List[User]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_id, name, membership_level, created_at, updated_at FROM users ORDER BY created_at DESC"
        )
        results = cursor.fetchall()
        conn.close()

        return [
            User(
                user_id=row[0],
                name=row[1],
                membership_level=MembershipLevel(row[2]),
                created_at=datetime.fromisoformat(row[3]),
                updated_at=datetime.fromisoformat(row[4])
            )
            for row in results
        ]

    def get_members_by_level(self, membership_level: MembershipLevel) -> List[User]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_id, name, membership_level, created_at, updated_at FROM users WHERE membership_level = ? ORDER BY created_at DESC",
            (membership_level.value,)
        )
        results = cursor.fetchall()
        conn.close()

        return [
            User(
                user_id=row[0],
                name=row[1],
                membership_level=MembershipLevel(row[2]),
                created_at=datetime.fromisoformat(row[3]),
                updated_at=datetime.fromisoformat(row[4])
            )
            for row in results
        ]
