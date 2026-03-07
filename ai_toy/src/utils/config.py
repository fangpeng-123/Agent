# -*- coding: utf-8 -*-
"""配置和常量"""

import yaml
from pathlib import Path
from enum import Enum


# 加载配置文件
CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f)
except Exception as e:
    print(f"[WARN] 加载配置文件失败: {e}，使用默认配置")
    _config = {}


class IntentType(Enum):
    """意图类型枚举"""

    DIRECT_CHAT = "direct_chat"
    TOOL_CALL = "tool_call"
    CLARIFICATION = "clarification"


# 获取系统提示词类型
SYSTEM_PROMPT_TYPE = _config.get("model", {}).get("system_prompt_type", "child_education")


def get_system_prompt() -> str:
    """根据配置获取系统提示词"""
    prompt_type = _config.get("model", {}).get("system_prompt_type", "child_education")

    if prompt_type == "child_education":
        from src.prompts.system_prompts.child_companion import CHILD_EDUCATION_PROMPT
        return CHILD_EDUCATION_PROMPT
    elif prompt_type == "child_companion":
        from src.prompts.system_prompts.child_companion import CHILD_EDUCATION_PROMPT
        return CHILD_EDUCATION_PROMPT
    elif prompt_type == "base":
        # 返回默认的基础提示词
        return MAIN_MODEL_SYSTEM_PROMPT
    else:
        # 默认使用儿童教育提示词
        from src.prompts.system_prompts.child_companion import CHILD_EDUCATION_PROMPT
        return CHILD_EDUCATION_PROMPT


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

可用工具：天气、地图、日期时间

工作原则：
1. 基于工具结果回答问题
2. 回答要口语化、自然，像朋友聊天一样
3. 不要使用Markdown格式（如**粗体**、#标题、-列表、代码块等）
4. 直接回答，简洁准确，不要加"根据查询结果"之类的开场白
5. 使用中文
6. 不要使用thinking思考标签，直接回答

示例：
用户：北京明天天气怎么样？
助手：北京明天晴天，气温3到15度，挺适合出门的。

用户：上海会下雨吗？
助手：上海今天不下雨，多云天气，气温10到18度。

用户：广州后天呢？
助手：后天广州有小雨，记得带伞，气温15到22度。

工具结果已包含在上文，直接根据结果回答。"""
