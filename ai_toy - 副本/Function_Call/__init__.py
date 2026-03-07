# -*- coding: utf-8 -*-
"""
Function Call工具整合包
包含天气和地图工具
"""

from .Weather import (
    WEATHER_TOOLS,
    WEATHER_FUNCTIONS,
    get_weather_now,
    get_weather_forecast,
    get_hourly_forecast,
    get_air_quality,
    get_life_index,
    search_city,
)

from .Map import (
    MAP_TOOLS,
    MAP_FUNCTIONS,
    geocode,
    reverse_geocode,
    place_search,
    get_direction,
    get_ip_location,
)

# 合并所有工具
ALL_TOOLS = WEATHER_TOOLS + MAP_TOOLS
ALL_FUNCTIONS = {**WEATHER_FUNCTIONS, **MAP_FUNCTIONS}

__all__ = [
    # 工具定义
    "WEATHER_TOOLS",
    "MAP_TOOLS",
    "ALL_TOOLS",
    # 函数字典
    "WEATHER_FUNCTIONS",
    "MAP_FUNCTIONS",
    "ALL_FUNCTIONS",
    # 天气函数
    "get_weather_now",
    "get_weather_forecast",
    "get_hourly_forecast",
    "get_air_quality",
    "get_life_index",
    "search_city",
    # 地图函数
    "geocode",
    "reverse_geocode",
    "place_search",
    "get_direction",
    "get_ip_location",
]
