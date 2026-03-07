# -*- coding: utf-8 -*-
"""意图识别模块"""

from typing import Any, Dict, List, Optional

from src.utils.config import COMMON_CITIES, GREETINGS, IntentType, TOOL_KEYWORDS
from src.utils import IntentResult


def extract_location(text: str) -> Optional[str]:
    """从文本中提取地点名称"""
    for city in COMMON_CITIES:
        if city in text:
            return city
    return None


def rule_based_intent_classify(user_input: str) -> IntentResult:
    """基于规则的意图分类（毫秒级，无需API调用）"""
    text = user_input
    suggested_tools = []
    extracted_params: Dict[str, Any] = {}

    location = extract_location(text)
    if location:
        extracted_params["location"] = location

    for tool, keywords in TOOL_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            if tool.startswith("get_weather") or tool == "search_city":
                suggested_tools.append(tool)

    if suggested_tools:
        return IntentResult(
            intent=IntentType.TOOL_CALL,
            confidence=0.95,
            reasoning=f"检测到天气关键词，地点：{location or '未识别'}",
            suggested_tools=suggested_tools,
            extracted_params=extracted_params,
        )

    for tool, keywords in TOOL_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            if tool not in [
                "get_weather_now",
                "get_weather_forecast",
                "get_air_quality",
            ]:
                suggested_tools.append(tool)

    if suggested_tools:
        return IntentResult(
            intent=IntentType.TOOL_CALL,
            confidence=0.9,
            reasoning="检测到地图相关关键词",
            suggested_tools=suggested_tools,
            extracted_params=extracted_params,
        )

    if any(g in text for g in GREETINGS):
        return IntentResult(
            intent=IntentType.DIRECT_CHAT,
            confidence=0.95,
            reasoning="检测到问候语",
        )

    return IntentResult(
        intent=IntentType.DIRECT_CHAT,
        confidence=0.7,
        reasoning="无法识别为工具调用，走直接对话",
    )
