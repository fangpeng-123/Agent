# -*- coding: utf-8 -*-
"""消息构建器"""

import json
from typing import Any, Dict, List, Optional

from src.utils.config import MAIN_MODEL_SYSTEM_PROMPT
from src.utils import ToolCall


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
