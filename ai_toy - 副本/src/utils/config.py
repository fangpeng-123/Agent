# -*- coding: utf-8 -*-
"""配置和常量"""

from enum import Enum


class IntentType(Enum):
    """意图类型枚举"""

    DIRECT_CHAT = "direct_chat"
    TOOL_CALL = "tool_call"
    CLARIFICATION = "clarification"


TOOL_KEYWORDS = {
    "get_weather_now": [
        "天气",
        "气温",
        "温度",
        "冷热",
        "下雨",
        "晴天",
        "阴天",
        "天气怎么样",
        "今天天气",
    ],
    "get_weather_forecast": ["预报", "未来", "明天", "后天", "周末天气", "未来几天"],
    "get_air_quality": ["空气质量", "AQI", "PM2.5", "空气污染"],
    "get_hourly_forecast": ["逐小时", "每小时"],
    "get_life_index": ["生活指数", "运动指数", "穿衣指数", "紫外线", "洗车指数"],
    "search_city": ["城市", "地点"],
    "geocode": ["地址转坐标", "经纬度"],
    "reverse_geocode": ["坐标转地址", "逆地理"],
    "place_search": ["附近", "搜索", "找", "餐厅", "酒店", "景点"],
    "get_direction": ["路线", "怎么走", "导航", "从", "到"],
    "get_ip_location": ["IP定位", "我的位置"],
}

COMMON_CITIES = [
    "北京",
    "上海",
    "广州",
    "深圳",
    "杭州",
    "南京",
    "武汉",
    "成都",
    "重庆",
    "西安",
    "苏州",
    "天津",
    "长沙",
    "郑州",
    "青岛",
    "合肥",
    "厦门",
    "宁波",
    "无锡",
    "福州",
    "昆明",
    "济南",
    "大连",
    "沈阳",
]

GREETINGS = ["你好", "hi", "hello", "在吗", "忙吗", "吃了吗", "再见", "拜拜"]

MAIN_MODEL_SYSTEM_PROMPT = """你是智能助手，帮助用户解答问题。

可用工具：天气、地图

工作原则：
1. 基于工具结果回答问题
2. 直接回答，简洁准确
3. 使用中文
4. 不要使用<think>思考标签，直接回答

工具结果已包含在上文，直接根据结果回答。"""
