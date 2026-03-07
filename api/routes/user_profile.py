# -*- coding: utf-8 -*-
"""用户画像接口"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import json
from pathlib import Path

router = APIRouter()

USER_PROFILE_DIR = Path("./data/user_profiles")


class UserProfileUpdate(BaseModel):
    """用户画像更新"""

    name: Optional[str] = None
    interests: list = []
    preferences: Dict = {}


@router.get("/{user_id}")
async def get_user_profile(user_id: str):
    """获取用户画像"""
    file_path = USER_PROFILE_DIR / f"user_{user_id}.json"
    if not file_path.exists():
        return {"user_id": user_id, "name": None, "interests": [], "preferences": {}}

    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


@router.put("/{user_id}")
async def update_user_profile(user_id: str, profile: UserProfileUpdate):
    """更新用户画像"""
    USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    file_path = USER_PROFILE_DIR / f"user_{user_id}.json"
    data = {
        "user_id": user_id,
        "name": profile.name,
        "interests": profile.interests,
        "preferences": profile.preferences,
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"success": True, "user_id": user_id}


@router.post("/{user_id}/interests")
async def add_interest(user_id: str, interest: str):
    """添加兴趣"""
    file_path = USER_PROFILE_DIR / f"user_{user_id}.json"
    data = {"user_id": user_id, "interests": []}

    if file_path.exists():
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

    if interest not in data["interests"]:
        data["interests"].append(interest)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"success": True, "interests": data["interests"]}
