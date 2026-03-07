# -*- coding: utf-8 -*-
"""消息构建器"""

import json
from typing import Any, Dict, List, Optional

from src.utils.config import get_system_prompt, MAIN_MODEL_SYSTEM_PROMPT
from src.utils import ToolCall
from Function_Call import get_user_profile
from Function_Call.UserProfile import USER_PROFILES


async def get_user_profile_content() -> str:
    """获取用户画像内容（完整JSON格式）"""
    try:
        user_id = "user_001"
        profile = USER_PROFILES.get(user_id, {})
        if profile:
            return f"用户画像：{json.dumps(profile, ensure_ascii=False, indent=2)}"
        else:
            return f"[用户画像获取失败] 未找到用户 {user_id} 的画像信息"
    except Exception as e:
        return f"[用户画像获取失败] {str(e)}"


class MessageBuilder:
    @staticmethod
    def create_system_message(content: str) -> Dict[str, str]:
        return {"role": "system", "content": content}

    @staticmethod
    def create_human_message(content: str) -> Dict[str, str]:
        return {"role": "user", "content": content}

    @staticmethod
    def create_ai_message(
        content: str, tool_calls: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        message = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return message

    @staticmethod
    def build_main_model_messages(
        user_input: str,
        tool_results: List[ToolCall],
        conversation_history: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        messages = [{"role": "system", "content": MAIN_MODEL_SYSTEM_PROMPT}]

        if conversation_history:
            messages.extend(conversation_history)

        if tool_results:
            tool_context = "工具调用结果：\n\n"
            for tc in tool_results:
                tool_context += f"[工具] {tc.tool_name}\n"
                tool_context += (
                    f"[参数] {json.dumps(tc.arguments, ensure_ascii=False)}\n"
                )
                tool_context += f"[结果] {tc.result}\n\n"
            messages.append(
                {"role": "user", "content": f"{tool_context}\n用户问题：{user_input}"}
            )
        else:
            messages.append({"role": "user", "content": user_input})

        return messages

    @staticmethod
    async def build_structured_messages(
        rewritten_query: str,
        tool_results: List[Dict],
        conversation_history: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """
        构建拆分格式的主模型消息（详细版）

        消息顺序：
        1. System message (系统提示词)
        2. User message (用户画像)
        3. User messages (工具调用结果)
        4. User message (用户原始输入和重写后的意图)
        5. User messages (最近对话历史)
        6. User message (回答请求)
        """
        recent_history = conversation_history[-15:] if conversation_history else []

        # 1. System message (系统提示词)
        system_prompt = get_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # 2. User message (用户画像)
        user_profile = await get_user_profile_content()
        messages.append({"role": "user", "content": user_profile})

        # 3. User messages (工具调用结果)
        if tool_results:
            for r in tool_results:
                use_tool = r.get("use_tool", False)
                tool_name = r.get("tool", "unknown")
                reason = r.get("reason", "")
                result = r.get("result", "")
                status = "使用工具" if use_tool else "不使用工具"
                messages.append(
                    {
                        "role": "user",
                        "content": f"[工具决策] {tool_name}: {status}\n原因: {reason}\n结果: {str(result)[:500]}",
                    }
                )

        # 4. User message (用户原始输入和重写后的意图)
        original_input = (
            conversation_history[-1]['content']
            if conversation_history and conversation_history[-1]['role'] == 'user'
            else rewritten_query
        )
        messages.append(
            {
                "role": "user",
                "content": f"用户原始输入: {original_input}\n重写后的意图: {rewritten_query}",
            }
        )

        # 5. User messages (最近对话历史)
        if recent_history:
            history_text = "\n=== 最近15轮对话历史 ===\n"
            for i, msg in enumerate(recent_history):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:300]
                history_text += f"[{i + 1}] {role}: {content}\n"
            messages.append({"role": "user", "content": history_text})

        # 6. User message (回答请求)
        messages.append({"role": "user", "content": f"请基于以上信息回答用户问题。"})

        return messages
