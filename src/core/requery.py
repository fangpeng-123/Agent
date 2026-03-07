# -*- coding: utf-8 -*-
"""ReQuery 意图识别模块"""

import json
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

from Function_Call import get_user_profile

load_dotenv()


def _clean_string(s: str) -> str:
    """移除无效的 Unicode 代理字符"""
    try:
        return s.encode("utf-8", "surrogatepass").decode("utf-8", errors="replace")
    except Exception:
        return s


def get_requery_model():
    """获取 ReQuery 模型"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    return ChatOpenAI(
        model="qwen3-30b-a3b-instruct-2507",
        # model="tongyi-intent-detect-v3",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(api_key) if api_key else None,
        temperature=0.3,
        extra_body={"enable_thinking": False},
    )


REQUERy_SYSTEM_PROMPT = """你是一个意图理解助手。

## 用户画像信息
{user_profile}

## 默认位置
用户所在城市：{default_location}
如果用户查询天气但未明确指定城市，请使用上述默认城市。

## 你的任务
理解用户的真实需求，将描述重写为清晰、完整的意图描述，并提取工具调用所需的参数。

## 可用工具
{tools_list}

## 输出格式
请以JSON格式输出：
{{
    "rewritten_query": "重写后的用户意图描述",
    "params": {{
        "location": "城市名称，如果用户未指定则使用默认城市",
        "query": "搜索关键词",
        "address": "地址",
        "origin": "起点",
        "destination": "终点",
        "days": 天数,
        "hours": 小时数,
        "region": "区域",
        "page_size": 返回数量,
        "lat": 纬度,
        "lng": 经度,
        "city_name": "城市名称",
        "country": "国家代码",
        "user_id": "用户ID，默认为user_001",
        "query_type": "日期时间查询类型：date/weekday/time/full"
    }}
}}

## 用户输入
{user_input}

请直接输出JSON。"""


class ReQueryResult:
    """ReQuery 结果"""

    def __init__(self, rewritten_query: str, params: Dict[str, Any]):
        self.rewritten_query = rewritten_query
        self.params = params


async def requery(user_input: str, available_tools: List[Dict]) -> ReQueryResult:
    """执行 ReQuery"""
    model = get_requery_model()

    user_profile = await get_user_profile("user_001")

    default_location = "合肥"
    for line in user_profile.split("\n"):
        if "[所在城市]" in line:
            default_location = line.split("]")[1].strip()
            break

    tools_description = "\n".join(
        [
            f"- {t['function']['name']}: {t['function']['description']}"
            for t in available_tools
        ]
    )

    clean_input = user_input.strip()

    prompt = (
        REQUERy_SYSTEM_PROMPT.replace("{user_profile}", user_profile)
        .replace("{default_location}", default_location)
        .replace("{tools_list}", tools_description)
        .replace("{user_input}", clean_input)
    )

    prompt = _clean_string(prompt)

    messages = [
        SystemMessage(content=_clean_string(prompt)),
        HumanMessage(content=_clean_string(clean_input)),
    ]

    response = await model.ainvoke(messages)

    try:
        content = response.content
        if isinstance(content, list):
            content = str(content)
        result = json.loads(content)
        return ReQueryResult(
            rewritten_query=result.get("rewritten_query", clean_input),
            params=result.get("params", {}),
        )
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        return ReQueryResult(rewritten_query=clean_input, params={})
