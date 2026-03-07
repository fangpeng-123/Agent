from typing import Optional
from datetime import datetime
import sqlite3
from pathlib import Path

from ..config import Config
from ..models.schemas import ReviewLevel, ReviewRequest


class ReviewService:
    def __init__(self, config: Config):
        self.config = config
        self.review_config = config.review
        self.db_path = "data/sqlite/review.db"
        self._init_db()

    def _init_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                question TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                review_level TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                reviewer_id TEXT,
                final_response TEXT,
                rejection_reason TEXT
            )
        """)

        conn.commit()
        conn.close()

    def add_to_queue(self, request: ReviewRequest) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO review_queue (user_id, question, ai_response, review_level)
            VALUES (?, ?, ?, ?)
            """,
            (request.user_id, request.question, request.ai_response, request.review_level.value)
        )

        review_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return review_id

    def get_pending_reviews(self) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, user_id, question, ai_response, review_level, created_at
            FROM review_queue
            WHERE status = 'pending'
            ORDER BY created_at ASC
            """
        )

        results = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "user_id": row[1],
                "question": row[2],
                "ai_response": row[3],
                "review_level": row[4],
                "created_at": row[5]
            }
            for row in results
        ]

    def approve_review(self, review_id: int, reviewer_id: str, final_response: Optional[str] = None) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if final_response:
            cursor.execute(
                """
                UPDATE review_queue
                SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP,
                    reviewer_id = ?, final_response = ?
                WHERE id = ?
                """,
                (reviewer_id, final_response, review_id)
            )
        else:
            cursor.execute(
                """
                UPDATE review_queue
                SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP,
                    reviewer_id = ?
                WHERE id = ?
                """,
                (reviewer_id, review_id)
            )

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def reject_review(self, review_id: int, reviewer_id: str, reason: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE review_queue
            SET status = 'rejected', reviewed_at = CURRENT_TIMESTAMP,
                reviewer_id = ?, rejection_reason = ?
            WHERE id = ?
            """,
            (reviewer_id, reason, review_id)
        )

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def get_review_status(self, review_id: int) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, user_id, question, ai_response, review_level, status,
                   created_at, reviewed_at, reviewer_id, final_response, rejection_reason
            FROM review_queue
            WHERE id = ?
            """,
            (review_id,)
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "id": result[0],
                "user_id": result[1],
                "question": result[2],
                "ai_response": result[3],
                "review_level": result[4],
                "status": result[5],
                "created_at": result[6],
                "reviewed_at": result[7],
                "reviewer_id": result[8],
                "final_response": result[9],
                "rejection_reason": result[10]
            }
        return None

    def get_user_reviews(self, user_id: str) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, question, ai_response, review_level, status,
                   created_at, reviewed_at, final_response
            FROM review_queue
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        )

        results = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "question": row[1],
                "ai_response": row[2],
                "review_level": row[3],
                "status": row[4],
                "created_at": row[5],
                "reviewed_at": row[6],
                "final_response": row[7]
            }
            for row in results
        ]

    def should_review(self, review_level: ReviewLevel) -> bool:
        if not self.review_config.enabled:
            return False

        level_config = self.review_config.levels.get(review_level.value, {})

        if level_config.get("auto_reply", False):
            return False

        if level_config.get("require_review", False):
            return True

        if level_config.get("sampling_review", False):
            return True

        return False
