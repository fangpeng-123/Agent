# -*- coding: utf-8 -*-
"""
Function Call工具整合包
包含天气和地图工具及其智能体
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

from .UserProfile import (
    USER_PROFILE_TOOLS,
    USER_PROFILE_FUNCTIONS,
    get_user_profile,
    PROFILE_AI_TOOLS,
    PROFILE_AI_FUNCTIONS,
    update_user_profile_ai,
)

from .DateTime import (
    DATETIME_TOOLS,
    DATETIME_FUNCTIONS,
    get_datetime_info,
)

from .weather_agents import WEATHER_AGENTS
from .map_agents import MAP_AGENTS
from .datetime_agents import DATETIME_AGENTS

ALL_TOOLS = (
    WEATHER_TOOLS + MAP_TOOLS + USER_PROFILE_TOOLS + DATETIME_TOOLS + PROFILE_AI_TOOLS
)
ALL_FUNCTIONS = {
    **WEATHER_FUNCTIONS,
    **MAP_FUNCTIONS,
    **USER_PROFILE_FUNCTIONS,
    **DATETIME_FUNCTIONS,
    **PROFILE_AI_FUNCTIONS,
}
ALL_AGENTS = {**WEATHER_AGENTS, **MAP_AGENTS, **DATETIME_AGENTS}

__all__ = [
    "WEATHER_TOOLS",
    "MAP_TOOLS",
    "USER_PROFILE_TOOLS",
    "DATETIME_TOOLS",
    "PROFILE_AI_TOOLS",
    "ALL_TOOLS",
    "WEATHER_FUNCTIONS",
    "MAP_FUNCTIONS",
    "USER_PROFILE_FUNCTIONS",
    "DATETIME_FUNCTIONS",
    "PROFILE_AI_FUNCTIONS",
    "ALL_FUNCTIONS",
    "get_weather_now",
    "get_weather_forecast",
    "get_hourly_forecast",
    "get_air_quality",
    "get_life_index",
    "search_city",
    "geocode",
    "reverse_geocode",
    "place_search",
    "get_direction",
    "get_ip_location",
    "get_user_profile",
    "update_user_profile_ai",
    "get_datetime_info",
    "WEATHER_AGENTS",
    "MAP_AGENTS",
    "DATETIME_AGENTS",
    "ALL_AGENTS",
]
