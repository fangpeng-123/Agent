# -*- coding: utf-8 -*-
"""
用户画像AI更新工具
使用AI模型分析对话内容，智能提取并更新用户画像信息
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from .user_profile_tools import USER_PROFILES

USER_PROFILES_FILE = Path(__file__).parent / "user_profiles.json"

PROFILE_AI_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "update_user_profile_ai",
            "description": "使用AI分析对话内容，智能提取并更新用户画像信息。适用于复杂上下文、多意图、模糊表达等规则难以处理的场景。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "用户ID，默认为user_001",
                        "default": "user_001",
                    },
                    "user_input": {"type": "string", "description": "用户的输入内容"},
                    "assistant_response": {
                        "type": "string",
                        "description": "AI助手的回复内容",
                    },
                },
                "required": ["user_id", "user_input"],
            },
        },
    }
]

PROFILE_AI_FUNCTIONS: Dict[str, Any] = {}


def load_user_profiles_from_file() -> Dict[str, Dict]:
    """从文件加载用户画像"""
    try:
        if USER_PROFILES_FILE.exists():
            with open(USER_PROFILES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] 加载用户画像文件失败: {e}")
    return {}


def save_user_profiles_to_file(profiles: Dict[str, Dict]) -> bool:
    """保存用户画像到文件"""
    try:
        with open(USER_PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] 保存用户画像失败: {e}")
        return False


def get_profile_prompt(user_id: str, user_input: str, assistant_response: str) -> str:
    """生成分析用户画像的prompt"""

    current_profile = USER_PROFILES.get(user_id, {})
    if not current_profile:
        loaded = load_user_profiles_from_file()
        current_profile = loaded.get(user_id, {})

    prompt = f"""你是一个用户画像分析专家。根据用户与AI的对话内容，提取需要更新的用户画像信息。

## 当前用户画像
{json.dumps(current_profile, ensure_ascii=False, indent=2)}

## 对话内容
用户：{user_input}
AI：{assistant_response}

## 分析要求
1. 只提取用户**明确表达**的本人信息（不是家人/朋友说的）
2. 忽略问句、事实陈述（如"今天吃了X"）、否定表达（如"不喜欢X"）
3. 判断每个信息字段的可信度（0-1）
4. 只返回需要更新的字段，不需要更新的字段不要返回

## 可提取的字段
- name: 用户姓名（如"我叫小明"）
- hobbies: 兴趣爱好（如"我喜欢跑步"）
- likes: 喜欢的事物（如"我喜欢榴莲"）
- character: 性格特点（如"我很开朗"）
- age: 年龄（如"我10岁"）
- gender: 性别（如"我是男孩"）
- location: 所在城市（如"我在合肥"）
- dislikes: 不喜欢的事物

## 输出格式（严格JSON，不要其他内容）
{{
    "updates": {{
        "字段名": "新值"
    }},
    "confidence": 0.0-1.0,
    "reason": "简短判断理由"
}}

如果对话中没有需要更新的信息，返回：
{{
    "updates": {{}},
    "confidence": 0.0,
    "reason": "对话中未发现需要更新的用户信息"
}}
"""
    return prompt


def parse_ai_response(response: str) -> Dict[str, Any]:
    """解析AI返回的JSON响应"""
    try:
        json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"[WARN] 解析AI响应失败: {e}")
    return {"updates": {}, "confidence": 0.0, "reason": "解析失败"}


async def update_user_profile_ai(
    user_id: str = "user_001", user_input: str = "", assistant_response: str = ""
) -> str:
    """
    使用AI分析对话内容，智能更新用户画像

    Args:
        user_id: 用户ID
        user_input: 用户输入
        assistant_response: AI回复

    Returns:
        更新结果
    """
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr
    import os
    from dotenv import load_dotenv

    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    if not user_input:
        return "用户输入为空，无需更新画像"

    try:
        prompt = get_profile_prompt(user_id, user_input, assistant_response)

        model = ChatOpenAI(
            model="qwen3-30b-a3b",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=SecretStr(API_KEY) if API_KEY else None,
            temperature=0.3,
            max_tokens=500,
            extra_body={"enable_thinking": False},
        )

        response = model.invoke(prompt)
        ai_response = (
            response.content if hasattr(response, "content") else str(response)
        )

        result = parse_ai_response(ai_response)

        if not result.get("updates") or result.get("confidence", 0) < 0.5:
            reason = result.get("reason", "未达到更新阈值")
            print(f"[INFO] 画像更新跳过: {reason}")
            return f"未发现需要更新的信息: {reason}"

        updates = result.get("updates", {})
        confidence = result.get("confidence", 0.5)
        reason = result.get("reason", "")

        loaded = load_user_profiles_from_file()
        USER_PROFILES.update(loaded)
        profile = USER_PROFILES.get(user_id, {})

        if not profile:
            return f"用户 {user_id} 不存在"

        updated_fields = []
        for field, value in updates.items():
            if field in profile and value:
                old_value = profile.get(field, "")

                if field == "name":
                    profile[field] = value
                    updated_fields.append(f"姓名: {value}")

                elif field in ["hobbies", "likes", "character"]:
                    if old_value:
                        existing = [
                            x.strip() for x in old_value.split("、") if x.strip()
                        ]
                        if value not in existing:
                            existing.append(value)
                            profile[field] = "、".join(existing)
                            updated_fields.append(f"{field}: +{value}")
                    else:
                        profile[field] = value
                        updated_fields.append(f"{field}: {value}")

                else:
                    profile[field] = value
                    updated_fields.append(f"{field}: {value}")

        if updated_fields:
            save_user_profiles_to_file(USER_PROFILES)
            result_msg = (
                f"[AI画像更新] {', '.join(updated_fields)} (置信度: {confidence:.2f})"
            )
            print(f"[OK] 用户 {user_id} 画像已更新: {result_msg}")
            return f"画像更新成功: {', '.join(updated_fields)}"
        else:
            return "没有需要更新的字段"

    except Exception as e:
        print(f"[ERROR] AI画像更新失败: {e}")
        return f"画像更新失败: {str(e)}"


PROFILE_AI_FUNCTIONS["update_user_profile_ai"] = update_user_profile_ai


if __name__ == "__main__":
    import asyncio

    print("[INFO] 用户画像AI更新工具测试")
    print("-" * 50)
    print(f"[OK] 已加载 {len(PROFILE_AI_TOOLS)} 个AI画像工具")
    print("\n可用工具:")
    for tool in PROFILE_AI_TOOLS:
        print(f"  - {tool['function']['name']}")
