# -*- coding: utf-8 -*-
"""
百度地图Function Call工具
提供地理位置和路线查询功能的函数调用实现
"""

import os
import httpx
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, List

# 加载环境变量
env_path = Path(__file__).parent / ".env"
agent_test_env_path = Path(__file__).parent.parent.parent / "agent_test" / ".env"

if env_path.exists():
    load_dotenv(env_path)
elif agent_test_env_path.exists():
    load_dotenv(agent_test_env_path)
else:
    load_dotenv()

BAIDU_MAP_AK = os.getenv("BAIDU_MAP_AK")

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


MAP_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "geocode",
            "description": "将地址转换为经纬度坐标，支持详细地址、地标、行政区划等",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "需要查询的地址，如'北京市海淀区中关村'",
                    }
                },
                "required": ["address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reverse_geocode",
            "description": "将经纬度坐标转换为详细地址信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "纬度坐标"},
                    "lng": {"type": "number", "description": "经度坐标"},
                },
                "required": ["lat", "lng"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "place_search",
            "description": "搜索POI地点，如餐厅、酒店、景点等",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "检索关键词，如'餐厅'、'酒店'、'景点'",
                    },
                    "region": {
                        "type": "string",
                        "description": "检索区域，如'北京'、'上海'，默认为全国",
                        "default": "全国",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "每页结果数量，默认为10",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_direction",
            "description": "获取两地之间的路线规划，支持驾车、步行、骑行、公交多种交通方式",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "起点地址或坐标，如'北京天安门'或'39.9042,116.4074'",
                    },
                    "destination": {
                        "type": "string",
                        "description": "终点地址或坐标，如'北京故宫'或'39.9163,116.3972'",
                    },
                    "mode": {
                        "type": "string",
                        "description": "交通方式，可选driving(驾车)、walking(步行)、riding(骑行)、transit(公交)",
                        "enum": ["driving", "walking", "riding", "transit"],
                        "default": "driving",
                    },
                },
                "required": ["origin", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ip_location",
            "description": "获取当前IP地址的地理位置信息，包括国家、省份、城市、经纬度等",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


# ============== 核心功能函数 ==============


async def geocode(address: str) -> str:
    """
    地理编码：将地址转换为经纬度坐标

    Args:
        address: 需要查询的地址，如"北京市海淀区中关村"

    Returns:
        经纬度坐标信息
    """
    if not BAIDU_MAP_AK:
        return "错误：未配置百度地图AK密钥"

    client = get_client()
    url = "https://api.map.baidu.com/geocoding/v3/"
    params = {"address": address, "output": "json", "ak": BAIDU_MAP_AK}

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("status") == 0:
            location = data["result"]["location"]
            return f"地址：{address}\n经度：{location['lng']}\n纬度：{location['lat']}\n精确度：{data['result'].get('precise', '未知')}"
        else:
            return f"地理编码失败：{data.get('msg', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


async def reverse_geocode(lat: float, lng: float) -> str:
    """
    逆地理编码：将经纬度转换为地址

    Args:
        lat: 纬度
        lng: 经度

    Returns:
        地址信息
    """
    if not BAIDU_MAP_AK:
        return "错误：未配置百度地图AK密钥"

    client = get_client()
    url = "https://api.map.baidu.com/reverse_geocoding/v3/"
    params = {"location": f"{lat},{lng}", "output": "json", "ak": BAIDU_MAP_AK}

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("status") == 0:
            result = data["result"]
            return f"经纬度：{lat}, {lng}\n地址：{result['formatted_address']}\n行政区划：{result['addressComponent']}"
        else:
            return f"逆地理编码失败：{data.get('msg', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


async def place_search(query: str, region: str = "全国", page_size: int = 10) -> str:
    """
    地点检索：搜索POI地点

    Args:
        query: 检索关键词，如"餐厅"
        region: 检索区域，默认为全国
        page_size: 每页结果数量，默认10

    Returns:
        地点搜索结果
    """
    if not BAIDU_MAP_AK:
        return "错误：未配置百度地图AK密钥"

    client = get_client()
    url = "https://api.map.baidu.com/place/v2/search"
    params = {
        "query": query,
        "region": region,
        "output": "json",
        "ak": BAIDU_MAP_AK,
        "page_size": page_size,
    }

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("status") == 0:
            results = data.get("results", [])
            if not results:
                return f"未找到'{query}'的相关地点"

            output = (
                f"搜索关键词：{query}\n区域：{region}\n共找到{len(results)}个结果：\n\n"
            )
            for i, place in enumerate(results, 1):
                output += f"{i}. {place.get('name', '未知')}\n"
                output += f"   地址：{place.get('address', '未知')}\n"
                output += f"   经度：{place.get('location', {}).get('lng', '未知')}\n"
                output += f"   纬度：{place.get('location', {}).get('lat', '未知')}\n\n"
            return output
        else:
            return f"地点检索失败：{data.get('msg', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


async def _parse_location(location: str) -> str:
    """
    解析位置输入，返回百度API要求的坐标格式（纬度,经度）

    Args:
        location: 地址字符串或坐标字符串

    Returns:
        坐标字符串，格式为"纬度,经度"
    """
    import re

    coord_pattern = r"^[\d.]+,[\d.]+$"
    if re.match(coord_pattern, location.strip()):
        parts = location.strip().split(",")
        lng = float(parts[0])
        lat = float(parts[1])
        if 73 < lng < 135 and 18 < lat < 54:
            return f"{lat},{lng}"
        else:
            return f"{lat},{lng}"

    geocode_result = await geocode(location)
    if "错误" in geocode_result or "失败" in geocode_result:
        raise ValueError(f"地址解析失败：{geocode_result}")

    lines = geocode_result.split("\n")
    lat, lng = None, None
    for line in lines:
        if line.startswith("经度："):
            lng = float(line.replace("经度：", "").strip())
        elif line.startswith("纬度："):
            lat = float(line.replace("纬度：", "").strip())

    if lat is None or lng is None:
        raise ValueError(f"无法从地理编码结果中提取坐标：{geocode_result}")

    return f"{lat},{lng}"


async def get_direction(origin: str, destination: str, mode: str = "driving") -> str:
    """
    路线规划：获取两地之间的路线

    Args:
        origin: 起点地址或坐标（支持"天安门"或"116.3972,39.9163"格式）
        destination: 终点地址或坐标
        mode: 交通方式，可选driving(驾车)、walking(步行)、riding(骑行)、transit(公交)

    Returns:
        路线规划结果
    """
    if not BAIDU_MAP_AK:
        return "错误：未配置百度地图AK密钥"

    mode_map = {
        "driving": "driving",
        "walking": "walking",
        "riding": "riding",
        "transit": "transit",
    }

    if mode not in mode_map:
        return (
            f"错误：不支持的交通方式'{mode}'，可选：driving、walking、riding、transit"
        )

    try:
        origin_coord = await _parse_location(origin)
        dest_coord = await _parse_location(destination)
    except ValueError as e:
        return f"位置解析失败：{str(e)}"

    client = get_client()
    url = f"https://api.map.baidu.com/directionlite/v1/{mode_map[mode]}"
    params = {
        "origin": origin_coord,
        "destination": dest_coord,
        "output": "json",
        "ak": BAIDU_MAP_AK,
    }

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("status") == 0:
            result = data.get("result", {})
            routes = result.get("routes", [])

            if not routes:
                return "未找到可用路线"

            route = routes[0]
            output = f"起点：{origin}\n终点：{destination}\n交通方式：{mode}\n\n"
            output += f"距离：{route.get('distance', '未知')}米\n"
            output += f"预计时间：{route.get('duration', '未知')}秒\n"

            if "steps" in route:
                output += "\n详细路线：\n"
                for i, step in enumerate(route["steps"], 1):
                    instruction = step.get("instruction", "")
                    if instruction:
                        output += f"{i}. {instruction}\n"

            return output
        else:
            status = data.get("status", "未知")
            msg = data.get("message", data.get("msg", "未知错误"))
            return f"路线规划失败：status={status}, message={msg}"
    except Exception as e:
        return f"请求异常：{str(e)}"


async def get_ip_location() -> str:
    """
    IP定位：获取当前IP的地理位置

    Returns:
        IP位置信息
    """
    if not BAIDU_MAP_AK:
        return "错误：未配置百度地图AK密钥"

    client = get_client()
    url = "https://api.map.baidu.com/location/ip"
    params = {"ak": BAIDU_MAP_AK, "coor": "bd09ll"}

    try:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("status") == 0:
            content = data.get("content", {})
            address_detail = content.get("address_detail", {})
            point = content.get("point", {})

            return (
                f"IP地址：{content.get('ip', '未知')}\n"
                f"国家：{address_detail.get('country', '未知')}\n"
                f"省份：{address_detail.get('province', '未知')}\n"
                f"城市：{address_detail.get('city', '未知')}\n"
                f"区县：{address_detail.get('district', '未知')}\n"
                f"经度：{point.get('x', '未知')}\n"
                f"纬度：{point.get('y', '未知')}\n"
                f"详细地址：{content.get('address', '未知')}"
            )
        else:
            return f"IP定位失败：{data.get('msg', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


# ============== 工具映射字典 ==============

MAP_FUNCTIONS = {
    "geocode": geocode,
    "reverse_geocode": reverse_geocode,
    "place_search": place_search,
    "get_direction": get_direction,
    "get_ip_location": get_ip_location,
}


if __name__ == "__main__":
    # 测试代码
    print("[INFO] 百度地图Function Call工具测试")
    print("-" * 50)
    print(f"[OK] 已加载 {len(MAP_TOOLS)} 个地图工具")
    print("\n可用工具列表：")
    for tool in MAP_TOOLS:
        print(
            f"  - {tool['function']['name']}: {tool['function']['description'][:40]}..."
        )
