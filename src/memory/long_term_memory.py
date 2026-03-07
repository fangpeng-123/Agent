# -*- coding: utf-8 -*-
"""长期记忆模块"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class LongTermMemory:
    """长期记忆管理器"""

    def __init__(self, storage_dir: str = "./data/user_profiles"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_user_profile(self, user_id: str, profile: Dict):
        """保存用户画像"""
        file_path = self.storage_dir / f"user_{user_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    def load_user_profile(self, user_id: str) -> Optional[Dict]:
        """加载用户画像"""
        file_path = self.storage_dir / f"user_{user_id}.json"
        if not file_path.exists():
            return None

        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def update_preference(self, user_id: str, key: str, value: any):
        """更新用户偏好"""
        profile = self.load_user_profile(user_id) or {}
        if "preferences" not in profile:
            profile["preferences"] = {}
        profile["preferences"][key] = value
        self.save_user_profile(user_id, profile)

    def add_interest(self, user_id: str, interest: str):
        """添加用户兴趣"""
        profile = self.load_user_profile(user_id) or {}
        if "interests" not in profile:
            profile["interests"] = []
        if interest not in profile["interests"]:
            profile["interests"].append(interest)
        self.save_user_profile(user_id, profile)

    def get_interests(self, user_id: str) -> List[str]:
        """获取用户兴趣"""
        profile = self.load_user_profile(user_id)
        return profile.get("interests", []) if profile else []
