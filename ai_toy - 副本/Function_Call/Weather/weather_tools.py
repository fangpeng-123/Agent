# -*- coding: utf-8 -*-
"""
和风天气Function Call工具
提供天气查询功能的函数调用实现
"""

import os
import httpx
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, List
from functools import lru_cache

# 加载环境变量
env_path = Path(__file__).parent / ".env"
agent_test_env_path = Path(__file__).parent.parent.parent / "agent_test" / ".env"

if env_path.exists():
    load_dotenv(env_path)
elif agent_test_env_path.exists():
    load_dotenv(agent_test_env_path)
else:
    load_dotenv()

HEFENG_KEY = os.getenv("HEFENG_KEY")
HEFENG_API_HOST = os.getenv("HEFENG_API_HOST")

# API地址配置
if HEFENG_API_HOST:
    BASE_URL = f"https://{HEFENG_API_HOST}/v7"
    GEO_URL = f"https://{HEFENG_API_HOST}/geo/v2"
else:
    BASE_URL = "https://devapi.qweather.com/v7"
    GEO_URL = "https://geoapi.qweather.com/geo/v2"

# 共享异步客户端
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
    return _client


# ============== 缓存LocationID ==============


@lru_cache(maxsize=128)
def _get_location_id_cached(location: str) -> str:
    """缓存版本的获取城市ID"""
    if location.isdigit():
        return location

    url = f"{GEO_URL}/city/lookup"
    params = {"location": location, "key": HEFENG_KEY, "range": "cn", "number": 1}

    try:
        response = httpx.get(url, params=params, timeout=5)
        data = response.json()

        if data.get("code") == "200":
            locations = data.get("location", [])
            if locations:
                return locations[0].get("id")
    except:
        pass

    return ""


async def get_location_id(location: str) -> str:
    """异步获取城市LocationID，如果是ID直接返回，否则搜索获取"""
    if location.isdigit():
        return location

    cached = _get_location_id_cached(location)
    if cached:
        return cached

    client = get_client()
    url = f"{GEO_URL}/city/lookup"
    params = {"location": location, "key": HEFENG_KEY, "range": "cn", "number": 1}

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("code") == "200":
            locations = data.get("location", [])
            if locations:
                return locations[0].get("id")
    except:
        pass

    return ""


WEATHER_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather_now",
            "description": "获取指定城市的实时天气情况，包括温度、天气状况、湿度、风向、风力、体感温度和能见度",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称或LocationID，如'北京'或'101010100'",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "获取指定城市的未来天气预报，支持3、7、10、15、30天的预报",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称或LocationID，如'北京'或'101010100'",
                    },
                    "days": {
                        "type": "integer",
                        "description": "预报天数，可选3、7、10、15、30，默认为3天",
                        "enum": [3, 7, 10, 15, 30],
                        "default": 3,
                    },
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hourly_forecast",
            "description": "获取指定城市的逐小时天气预报，支持24小时或72小时预报",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称或LocationID，如'北京'或'101010100'",
                    },
                    "hours": {
                        "type": "integer",
                        "description": "预报小时数，可选24或72，默认为24小时",
                        "enum": [24, 72],
                        "default": 24,
                    },
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_air_quality",
            "description": "获取指定城市的实时空气质量，包括AQI指数、PM2.5、PM10等指标",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称或LocationID，如'北京'或'101010100'",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_life_index",
            "description": "获取指定城市的生活指数建议，包括运动、洗车、穿衣、紫外线、旅游、舒适度、感冒指数",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称或LocationID，如'北京'或'101010100'",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_city",
            "description": "搜索城市信息，返回城市名称、ID、所属行政区划、经纬度等信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city_name": {"type": "string", "description": "要搜索的城市名称"},
                    "country": {
                        "type": "string",
                        "description": "国家代码，默认CN（中国）",
                        "default": "CN",
                    },
                },
                "required": ["city_name"],
            },
        },
    },
]


# ============== 核心功能函数 ==============


def _get_location_id(location: str) -> str:
    """
    获取城市LocationID，如果是ID直接返回，否则搜索获取
    """
    if location.isdigit():
        return location

    url = f"{GEO_URL}/city/lookup"
    params = {"location": location, "key": HEFENG_KEY, "range": "cn", "number": 1}

    try:
        response = httpx.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("code") == "200":
            locations = data.get("location", [])
            if locations:
                return locations[0].get("id")
    except:
        pass

    return ""


async def get_weather_now(location: str) -> str:
    """
    获取指定城市的实时天气情况

    Args:
        location: 城市名称或LocationID，如"北京"或"101010100"

    Returns:
        实时天气信息
    """
    if not HEFENG_KEY:
        return "错误：未配置和风天气KEY密钥"

    location_id = await get_location_id(location)
    if not location_id:
        return f"错误：无法找到城市'{location}'"

    client = get_client()
    url = f"{BASE_URL}/weather/now"
    params = {"location": location_id, "key": HEFENG_KEY}

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("code") == "200":
            now = data.get("now", {})
            return (
                f"[位置] {location} 实时天气\n"
                f"[温度] {now.get('temp', '未知')}°C\n"
                f"[天气] {now.get('text', '未知')}\n"
                f"[湿度] {now.get('humidity', '未知')}%\n"
                f"[风向] {now.get('windDir', '未知')}\n"
                f"[风力] {now.get('windScale', '未知')}级\n"
                f"[体感温度] {now.get('feelsLike', '未知')}°C\n"
                f"[能见度] {now.get('vis', '未知')}公里"
            )
        else:
            return f"查询失败：{data.get('code', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


async def get_weather_forecast(location: str, days: int = 3) -> str:
    """
    获取指定城市的未来天气预报

    Args:
        location: 城市名称或LocationID，如"北京"或"101010100"
        days: 预报天数，可选3、7、10、15、30，默认3天

    Returns:
        天气预报信息
    """
    if not HEFENG_KEY:
        return "错误：未配置和风天气KEY密钥"

    location_id = await get_location_id(location)
    if not location_id:
        return f"错误：无法找到城市'{location}'"

    valid_days = [3, 7, 10, 15, 30]
    if days not in valid_days:
        return f"错误：days参数必须是 {valid_days} 之一"

    client = get_client()
    url = f"{BASE_URL}/weather/{days}d"
    params = {"location": location_id, "key": HEFENG_KEY}

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("code") == "200":
            daily = data.get("daily", [])
            if not daily:
                return "未获取到预报数据"

            output = f"[位置] {location} {days}天天气预报\n\n"
            for day in daily:
                output += (
                    f"[日期] {day.get('fxDate', '未知')}\n"
                    f"   [白天] {day.get('textDay', '未知')}  {day.get('tempMax', '未知')}°C\n"
                    f"   [夜间] {day.get('textNight', '未知')}  {day.get('tempMin', '未知')}°C\n"
                    f"   [风向] {day.get('windDirDay', '未知')} {day.get('windScaleDay', '未知')}级\n"
                    f"   [降水概率] {day.get('precip', '未知')}mm\n\n"
                )
            return output
        else:
            return f"查询失败：{data.get('code', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


async def get_hourly_forecast(location: str, hours: int = 24) -> str:
    """
    获取指定城市的逐小时天气预报

    Args:
        location: 城市名称或LocationID，如"北京"或"101010100"
        hours: 预报小时数，可选24或72，默认24小时

    Returns:
        逐小时天气预报信息
    """
    if not HEFENG_KEY:
        return "错误：未配置和风天气KEY密钥"

    location_id = await get_location_id(location)
    if not location_id:
        return f"错误：无法找到城市'{location}'"

    valid_hours = [24, 72]
    if hours not in valid_hours:
        return f"错误：hours参数必须是 {valid_hours} 之一"

    client = get_client()
    url = f"{BASE_URL}/weather/{hours}h"
    params = {"location": location_id, "key": HEFENG_KEY}

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("code") == "200":
            hourly = data.get("hourly", [])
            if not hourly:
                return "未获取到预报数据"

            output = f"[位置] {location} 未来{hours}小时天气预报\n\n"
            for i, hour in enumerate(hourly[:12]):
                output += (
                    f"[时间] {hour.get('fxTime', '未知')[11:16]}\n"
                    f"   [温度] {hour.get('temp', '未知')}°C\n"
                    f"   [天气] {hour.get('text', '未知')}\n"
                    f"   [风向] {hour.get('windDir', '未知')} {hour.get('windScale', '未知')}级\n"
                    f"   [降水概率] {hour.get('pop', '未知')}%\n\n"
                )
            return output
        else:
            return f"查询失败：{data.get('code', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


async def get_air_quality(location: str) -> str:
    """
    获取指定城市的实时空气质量

    Args:
        location: 城市名称或LocationID，如"北京"或"101010100"

    Returns:
        空气质量信息
    """
    if not HEFENG_KEY:
        return "错误：未配置和风天气KEY密钥"

    location_id = await get_location_id(location)
    if not location_id:
        return f"错误：无法找到城市'{location}'"

    client = get_client()
    url = f"{BASE_URL}/air/now"
    params = {"location": location_id, "key": HEFENG_KEY}

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("code") == "200":
            now = data.get("now", {})
            aqi = now.get("aqi", "未知")
            category = now.get("category", "未知")

            return (
                f"[位置] {location} 空气质量\n"
                f"[AQI指数] {aqi}\n"
                f"[等级] {category}\n"
                f"[PM2.5] {now.get('pm2p5', '未知')} μg/m³\n"
                f"[PM10] {now.get('pm10', '未知')} μg/m³\n"
                f"[NO2] {now.get('no2', '未知')} μg/m³\n"
                f"[SO2] {now.get('so2', '未知')} μg/m³\n"
                f"[CO] {now.get('co', '未知')} mg/m³\n"
                f"[O3] {now.get('o3', '未知')} μg/m³"
            )
        else:
            return f"查询失败：{data.get('code', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


async def get_life_index(location: str) -> str:
    """
    获取指定城市的生活指数建议

    Args:
        location: 城市名称或LocationID，如"北京"或"101010100"

    Returns:
        生活指数信息
    """
    if not HEFENG_KEY:
        return "错误：未配置和风天气KEY密钥"

    location_id = await get_location_id(location)
    if not location_id:
        return f"错误：无法找到城市'{location}'"

    client = get_client()
    url = f"{BASE_URL}/indices/1d"
    params = {
        "location": location_id,
        "key": HEFENG_KEY,
        "type": "1,2,3,5,6,8,9",
    }

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("code") == "200":
            daily = data.get("daily", [])
            if not daily:
                return "未获取到指数数据"

            output = f"[位置] {location} 今日生活指数\n\n"
            index_names = {
                "1": "[运动指数]",
                "2": "[洗车指数]",
                "3": "[穿衣指数]",
                "5": "[紫外线指数]",
                "6": "[旅游指数]",
                "8": "[舒适度指数]",
                "9": "[感冒指数]",
            }

            for index in daily:
                index_type = index.get("type", "")
                name = index_names.get(index_type, index_type)
                output += f"{name}：{index.get('category', '未知')}\n"
                output += f"   建议：{index.get('text', '暂无建议')}\n\n"

            return output
        else:
            return f"查询失败：{data.get('code', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


async def search_city(city_name: str, country: str = "CN") -> str:
    """
    搜索城市信息

    Args:
        city_name: 城市名称
        country: 国家代码，默认CN（中国）

    Returns:
        搜索结果
    """
    if not HEFENG_KEY:
        return "错误：未配置和风天气KEY密钥"

    client = get_client()
    url = f"{GEO_URL}/city/lookup"
    params = {
        "location": city_name,
        "key": HEFENG_KEY,
        "range": "cn" if country == "CN" else "world",
        "number": 10,
    }

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("code") == "200":
            locations = data.get("location", [])
            if not locations:
                return f"未找到城市'{city_name}'"

            output = f"[搜索] '{city_name}' 搜索结果：\n\n"
            for i, loc in enumerate(locations, 1):
                output += (
                    f"{i}. {loc.get('name', '未知')}\n"
                    f"   ID：{loc.get('id', '未知')}\n"
                    f"   所属：{loc.get('adm1', '')} {loc.get('adm2', '')}\n"
                    f"   国家：{loc.get('country', '未知')}\n"
                    f"   经纬度：{loc.get('lon', '未知')}, {loc.get('lat', '未知')}\n\n"
                )
            return output
        else:
            return f"搜索失败：{data.get('code', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


# ============== 工具映射字典 ==============

WEATHER_FUNCTIONS = {
    "get_weather_now": get_weather_now,
    "get_weather_forecast": get_weather_forecast,
    "get_hourly_forecast": get_hourly_forecast,
    "get_air_quality": get_air_quality,
    "get_life_index": get_life_index,
    "search_city": search_city,
}


if __name__ == "__main__":
    # 测试代码
    print("[INFO] 和风天气Function Call工具测试")
    print("-" * 50)
    print(f"[OK] 已加载 {len(WEATHER_TOOLS)} 个天气工具")
    print("\n可用工具列表：")
    for tool in WEATHER_TOOLS:
        print(
            f"  - {tool['function']['name']}: {tool['function']['description'][:40]}..."
        )
