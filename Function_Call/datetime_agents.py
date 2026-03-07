# -*- coding: utf-8 -*-
"""日期时间工具智能体"""

import json
from typing import Dict, Any
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


class DatetimeAgent:
    """日期时间工具智能体"""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.model = get_agent_model()
        from .agent_prompts import DATETIME_AGENT_PROMPTS

        self.system_prompt = DATETIME_AGENT_PROMPTS.get(tool_name, "")

    async def run(self, user_input: str, requery_params: Dict) -> Dict[str, Any]:
        """执行智能体判断"""
        prompt_content = self.system_prompt.replace("{input}", user_input).replace(
            "{params}", json.dumps(requery_params, ensure_ascii=False)
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

        if result.get("use_tool", False):
            try:
                from .DateTime import get_datetime_info

                query_type = self._extract_query_type(requery_params, user_input)
                result["result"] = await get_datetime_info(query_type)
            except Exception as e:
                result["result"] = f"工具执行失败: {str(e)}"

        return result

    def _extract_query_type(self, requery_params: Dict, user_input: str) -> str:
        """从参数或用户输入中提取查询类型"""
        if "query_type" in requery_params:
            return requery_params["query_type"]

        text = user_input.lower()
        if "星期" in text or "周几" in text or "周几" in text:
            return "weekday"
        elif "时间" in text or "几点" in text:
            return "time"
        elif "日期" in text or "几号" in text or "哪天" in text:
            return "date"
        else:
            return "full"


class GetDatetimeInfoAgent(DatetimeAgent):
    """日期时间查询智能体"""

    def __init__(self):
        super().__init__("get_datetime_info")


DATETIME_AGENTS = {
    "get_datetime_info": GetDatetimeInfoAgent(),
}
