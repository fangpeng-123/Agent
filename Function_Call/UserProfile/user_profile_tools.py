# -*- coding: utf-8 -*-
"""
用户画像Function Call工具
提供用户画像查询功能的函数调用实现
"""

from typing import Dict, Any, List

USER_PROFILES: Dict[str, Dict] = {
    "user_001": {
        "user_id": "user_001",
        "name": "坤坤",  # 待填写
        "age": "10",
        "gender": "男",
        "birthday": "2017/03/15",
        "character": "开朗、有活力的人，喜欢和新的人互动。",
        "hobbies": "旅游、运动、阅读",
        "likes": "美食、运动、新的技术",
        "dislikes": "压力大、工作繁忙",
        "relationship": "与其他小朋友保持良好的关系",
        "location": "合肥",
    }
}

USER_PROFILE_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "获取用户画像信息，包括姓名、年龄、性别、生日、性格、爱好、喜欢的事、不喜欢的事、人际关系、所在城市等",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "用户ID，默认为user_001",
                        "default": "user_001",
                    }
                },
                "required": ["user_id"],
            },
        },
    },
]

USER_PROFILE_FUNCTIONS = {
    "get_user_profile": None,
}


async def get_user_profile(user_id: str = "user_001") -> str:
    """
    获取用户画像信息

    Args:
        user_id: 用户ID，默认为user_001

    Returns:
        用户画像信息
    """
    profile = USER_PROFILES.get(user_id)

    if not profile:
        return f"错误：未找到用户'{user_id}'的画像信息"

    output = f"[用户画像] {user_id}\n\n"
    output += f"[姓名] {profile.get('name', '未填写')}\n"
    output += f"[年龄] {profile.get('age', '未填写')}\n"
    output += f"[性别] {profile.get('gender', '未填写')}\n"
    output += f"[生日] {profile.get('birthday', '未填写')}\n"
    output += f"[性格] {profile.get('character', '未填写')}\n"
    output += f"[爱好] {profile.get('hobbies', '未填写')}\n"
    output += f"[喜欢的事] {profile.get('likes', '未填写')}\n"
    output += f"[不喜欢的事] {profile.get('dislikes', '未填写')}\n"
    output += f"[人际关系] {profile.get('relationship', '未填写')}\n"
    output += f"[所在城市] {profile.get('location', '未填写')}\n"

    return output


USER_PROFILE_FUNCTIONS["get_user_profile"] = get_user_profile


if __name__ == "__main__":
    print("[INFO] 用户画像Function Call工具测试")
    print("-" * 50)
    print(f"[OK] 已加载 {len(USER_PROFILE_TOOLS)} 个用户画像工具")
    print("\n可用工具列表：")
    for tool in USER_PROFILE_TOOLS:
        print(
            f"  - {tool['function']['name']}: {tool['function']['description'][:40]}..."
        )
    print("\n测试用户画像查询：")
    import asyncio

    result = asyncio.run(get_user_profile("user_001"))
    print(result)
