"""
百度地图MCP服务
使用百度地图API提供地理位置和路线查询功能
"""

from fastmcp import FastMCP
import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

# 加载 MCP 服务目录下的 .env 文件，如果不存在则尝试加载 agent_test 目录下的
mcp_env_path = Path(__file__).parent / ".env"
agent_test_env_path = Path(__file__).parent.parent.parent / "agent_test" / ".env"

if mcp_env_path.exists():
    load_dotenv(mcp_env_path)
elif agent_test_env_path.exists():
    load_dotenv(agent_test_env_path)
else:
    load_dotenv()

BAIDU_MAP_AK = os.getenv("BAIDU_MAP_AK")

mcp = FastMCP("BaiduMap")


@mcp.tool()
def geocode(address: str) -> str:
    """
    地理编码：将地址转换为经纬度坐标

    Args:
        address: 需要查询的地址，如"北京市海淀区中关村"

    Returns:
        经纬度坐标信息
    """
    if not BAIDU_MAP_AK:
        return "错误：未配置百度地图AK密钥"

    url = "https://api.map.baidu.com/geocoding/v3/"
    params = {"address": address, "output": "json", "ak": BAIDU_MAP_AK}

    try:
        response = httpx.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") == 0:
            location = data["result"]["location"]
            return f"地址：{address}\n经度：{location['lng']}\n纬度：{location['lat']}\n精确度：{data['result'].get('precise', '未知')}"
        else:
            return f"地理编码失败：{data.get('msg', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


@mcp.tool()
def reverse_geocode(lat: float, lng: float) -> str:
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

    url = "https://api.map.baidu.com/reverse_geocoding/v3/"
    params = {"location": f"{lat},{lng}", "output": "json", "ak": BAIDU_MAP_AK}

    try:
        response = httpx.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") == 0:
            result = data["result"]
            return f"经纬度：{lat}, {lng}\n地址：{result['formatted_address']}\n行政区划：{result['addressComponent']}"
        else:
            return f"逆地理编码失败：{data.get('msg', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


@mcp.tool()
def place_search(query: str, region: str = "全国", page_size: int = 10) -> str:
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

    url = "https://api.map.baidu.com/place/v2/search"
    params = {
        "query": query,
        "region": region,
        "output": "json",
        "ak": BAIDU_MAP_AK,
        "page_size": page_size,
    }

    try:
        response = httpx.get(url, params=params, timeout=10)
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


@mcp.tool()
def get_direction(origin: str, destination: str, mode: str = "driving") -> str:
    """
    路线规划：获取两地之间的路线

    Args:
        origin: 起点地址或坐标
        destination: 终点地址或坐标
        mode: 交通方式，可选 driving(驾车)、walking(步行)、riding(骑行)、transit(公交)

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

    url = f"https://api.map.baidu.com/direction/v2/{mode_map[mode]}"
    params = {
        "origin": origin,
        "destination": destination,
        "output": "json",
        "ak": BAIDU_MAP_AK,
    }

    try:
        response = httpx.get(url, params=params, timeout=10)
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
                    output += f"{i}. {step.get('instruction', '')}\n"

            return output
        else:
            return f"路线规划失败：{data.get('msg', '未知错误')}"
    except Exception as e:
        return f"请求异常：{str(e)}"


@mcp.tool()
def get_ip_location() -> str:
    """
    IP定位：获取当前IP的地理位置

    Returns:
        IP位置信息
    """
    if not BAIDU_MAP_AK:
        return "错误：未配置百度地图AK密钥"

    url = "https://api.map.baidu.com/location/ip"
    params = {"ak": BAIDU_MAP_AK, "coor": "bd09ll"}

    try:
        response = httpx.get(url, params=params, timeout=10)
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


if __name__ == "__main__":
    print("百度地图MCP服务已启动...")
    mcp.run(transport="stdio")
