# -*- coding: utf-8 -*-
"""用户画像工具智能体"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()


def get_agent_model():
    """获取工具智能体模型"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    return ChatOpenAI(
        model="qwen3-30b-a3b",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(api_key) if api_key else None,
        temperature=0.1,
        extra_body={"enable_thinking": False},
    )


# 用户画像数据文件路径
USER_PROFILES_FILE = Path(__file__).parent / "UserProfile" / "user_profiles.json"


def load_user_profiles_from_file() -> Dict[str, Dict]:
    """从文件加载用户画像"""
    try:
        if USER_PROFILES_FILE.exists():
            with open(USER_PROFILES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] 加载用户画像文件失败: {e}")
    return {}


def get_current_profile(user_id: str = "user_001") -> Dict[str, Any]:
    """获取当前用户画像"""
    profiles = load_user_profiles_from_file()
    return profiles.get(user_id, {})


# 延迟导入，避免循环依赖
_PROFILE_AGENT_PROMPTS = None


def _get_profile_agent_prompts():
    """延迟加载 PROFILE_AGENT_PROMPTS"""
    global _PROFILE_AGENT_PROMPTS
    if _PROFILE_AGENT_PROMPTS is None:
        from .agent_prompts import PROFILE_AGENT_PROMPTS as p

        _PROFILE_AGENT_PROMPTS = p
    return _PROFILE_AGENT_PROMPTS


class ProfileAgent:
    """用户画像更新智能体"""

    def __init__(self):
        self.model = get_agent_model()
        self.tool_name = "update_user_profile_ai"
        prompts = _get_profile_agent_prompts()
        self.system_prompt = prompts.get(self.tool_name, "")

    async def run(self, user_input: str, requery_params: Dict) -> Dict[str, Any]:
        """执行智能体判断"""
        # 获取当前用户画像
        current_profile = get_current_profile()

        # 构建 prompt
        prompt_content = self.system_prompt.replace("{input}", user_input).replace(
            "{current_profile}",
            json.dumps(current_profile, ensure_ascii=False, indent=2),
        )

        messages = [
            SystemMessage(content=prompt_content),
            HumanMessage(content=user_input),
        ]

        response = await self.model.ainvoke(messages)

        try:
            content = response.content
            if isinstance(content, list):
                content = str(content)
            result = json.loads(content)
        except (json.JSONDecodeError, TypeError, ValueError):
            result = {"use_tool": False, "reason": "JSON解析失败", "result": None}

        # 如果决定使用工具，直接执行更新逻辑
        if result.get("use_tool", False):
            try:
                # 直接执行更新逻辑，而不是调用 update_user_profile_ai（避免二次LLM调用）
                result["result"] = await self._do_update_profile(
                    user_input=user_input,
                    assistant_response=requery_params.get("assistant_response", ""),
                )
            except Exception as e:
                result["result"] = f"画像更新失败: {str(e)}"

        return result

    async def _do_update_profile(self, user_input: str, assistant_response: str) -> str:
        """使用LLM执行画像更新逻辑"""
        # 加载当前画像
        from .UserProfile.user_profile_tools import USER_PROFILES

        loaded = load_user_profiles_from_file()
        USER_PROFILES.update(loaded)
        profile = USER_PROFILES.get("user_001", {})

        if not profile:
            return "用户不存在"

        # 构建LLM分析prompt
        prompt = self._build_update_prompt(user_input, assistant_response, profile)

        # 调用LLM分析
        response = await self.model.ainvoke(prompt)

        try:
            content = response.content
            if isinstance(content, list):
                content = str(content)

            import re

            json_match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())

                # LLM可能直接返回updates，也可能返回嵌套结构
                if "updates" in parsed:
                    updates = parsed.get("updates", {})
                else:
                    # LLM直接返回了字段，没有嵌套
                    updates = parsed
            else:
                return "未发现需要更新的信息"
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            return f"解析失败: {str(e)}"

        if not updates:
            return "未发现需要更新的信息"

        # 执行更新
        updated_fields = []

        for field, value in updates.items():
            if not value:
                continue

            old_value = profile.get(field, "")

            if field == "name":
                # 姓名直接覆盖
                if value != old_value:
                    profile["name"] = value
                    updated_fields.append(f"姓名: {value}")

            elif field in ["hobbies", "likes", "character"]:
                # 列表型字段：追加新值，去重
                if old_value:
                    existing = [x.strip() for x in old_value.split("、") if x.strip()]
                else:
                    existing = []

                # 支持多种分隔符
                new_values = [
                    x.strip() for x in value.replace(",", "、").split("、") if x.strip()
                ]

                added = []
                for v in new_values:
                    if v not in existing:
                        existing.append(v)
                        added.append(v)

                if added:
                    profile[field] = "、".join(existing)
                    for a in added:
                        updated_fields.append(f"{field}: +{a}")

            else:
                # 其他字段直接覆盖
                if value != old_value:
                    profile[field] = value
                    updated_fields.append(f"{field}: {value}")

        # 保存
        if updated_fields:
            save_user_profiles_to_file(USER_PROFILES)
            return f"画像更新成功: {', '.join(updated_fields)}"

        return "未发现需要更新的信息"

    def _build_update_prompt(
        self, user_input: str, assistant_response: str, profile: Dict
    ) -> list:
        """构建LLM分析prompt"""
        prompt_content = f"""你是一个用户画像更新专家。根据用户与AI的对话内容，提取需要更新的用户画像信息。

## 当前用户画像
{json.dumps(profile, ensure_ascii=False, indent=2)}

## 对话内容
用户：{user_input}
AI：{assistant_response}

## 你的任务
1. 分析用户是否在表达自己的偏好（兴趣爱好、喜欢的事物、性格特点等）
2. 判断这些偏好是否已经在当前画像中存在
3. 只返回画像中不存在的新偏好

## 提取规则
- name: 用户姓名（如"我叫小明"）
- hobbies: 兴趣爱好（如"我喜欢跑步"、"我爱画画"）
- likes: 喜欢的事物（如"我喜欢吃苹果"、"我喜欢小动物"）
- character: 性格特点（如"我很开朗"、"我比较内向"）
- age: 年龄（如"我10岁"）
- gender: 性别（如"我是男孩"）
- location: 所在城市（如"我在合肥"）

## 重要规则
1. 只提取**明确表达**的偏好，跳过问句、否定表达、第三方提及
2. 比较是否已存在时，要考虑语义相似（如"阅读"和"看书"算同一爱好）
3. 如果画像中已有相关类别的新爱好，可以追加到现有值后面

## 输出格式（严格JSON）
{{
    "updates": {{
        "字段名": "新值"
    }}
}}

如果用户没有表达新偏好，返回：
{{
    "updates": {{}}
}}

请直接输出JSON，不要其他内容。"""

        from langchain_core.messages import SystemMessage, HumanMessage

        return [
            SystemMessage(content=prompt_content),
            HumanMessage(content=user_input),
        ]


def save_user_profiles_to_file(profiles) -> bool:
    """保存用户画像到文件"""
    try:
        with open(USER_PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] 保存用户画像失败: {e}")
        return False


# 全局单例
_profile_agent: Optional[ProfileAgent] = None


def get_profile_agent() -> ProfileAgent:
    """获取用户画像智能体实例"""
    global _profile_agent
    if _profile_agent is None:
        _profile_agent = ProfileAgent()
    return _profile_agent


PROFILE_AGENTS = {
    "update_user_profile_ai": get_profile_agent(),
}
