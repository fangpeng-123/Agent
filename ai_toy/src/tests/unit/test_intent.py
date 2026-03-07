# -*- coding: utf-8 -*-
"""意图分类单元测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.intent_classification import rule_based_intent_classify


def test_weather_intent():
    """测试天气意图识别"""
    result = rule_based_intent_classify("合肥今天天气怎么样？")
    assert result.intent.value == "tool_call"
    assert "get_weather_now" in result.suggested_tools


def test_greeting_intent():
    """测试问候意图"""
    result = rule_based_intent_classify("你好！")
    assert result.intent.value == "direct_chat"


def test_location_extraction():
    """测试地点提取"""
    result = rule_based_intent_classify("北京明天天气如何？")
    assert result.extracted_params.get("location") == "北京"


if __name__ == "__main__":
    test_weather_intent()
    test_greeting_intent()
    test_location_extraction()
    print("所有测试通过！")
