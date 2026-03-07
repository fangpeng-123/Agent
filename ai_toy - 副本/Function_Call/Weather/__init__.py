# -*- coding: utf-8 -*-
"""
和风天气Function Call工具包
"""

from .weather_tools import (
    WEATHER_TOOLS,
    WEATHER_FUNCTIONS,
    get_weather_now,
    get_weather_forecast,
    get_hourly_forecast,
    get_air_quality,
    get_life_index,
    search_city,
)

__all__ = [
    "WEATHER_TOOLS",
    "WEATHER_FUNCTIONS",
    "get_weather_now",
    "get_weather_forecast",
    "get_hourly_forecast",
    "get_air_quality",
    "get_life_index",
    "search_city",
]
