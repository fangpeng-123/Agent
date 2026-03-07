# -*- coding: utf-8 -*-
"""
百度地图MCP服务测试
测试各个工具是否能正常调用
"""

import asyncio
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import (
    mcp,
    geocode,
    reverse_geocode,
    place_search,
    get_direction,
    get_ip_location,
)


def test_geocode():
    """测试地理编码功能"""
    print("\n" + "=" * 60)
    print("测试 1: 地理编码 (geocode)")
    print("=" * 60)

    test_cases = [
        "北京市天安门",
        "上海市外滩",
        "InvalidAddress123",  # 测试无效地址
    ]

    for address in test_cases:
        print(f"\n输入地址: {address}")
        try:
            result = geocode(address)
            print(f"结果:\n{result}")
        except Exception as e:
            print(f"错误: {e}")


def test_reverse_geocode():
    """测试逆地理编码功能"""
    print("\n" + "=" * 60)
    print("测试 2: 逆地理编码 (reverse_geocode)")
    print("=" * 60)

    test_cases = [
        (39.9042, 116.4074),  # 北京天安门附近
        (31.2304, 121.4737),  # 上海市中心
        (0, 0),  # 无效坐标
    ]

    for lat, lng in test_cases:
        print(f"\n输入坐标: 纬度={lat}, 经度={lng}")
        try:
            result = reverse_geocode(lat, lng)
            print(f"结果:\n{result}")
        except Exception as e:
            print(f"错误: {e}")


def test_place_search():
    """测试地点搜索功能"""
    print("\n" + "=" * 60)
    print("测试 3: 地点搜索 (place_search)")
    print("=" * 60)

    test_cases = [
        ("肯德基", "北京", 3),
        ("星巴克", "上海", 5),
    ]

    for query, region, page_size in test_cases:
        print(f"\n搜索: {query} 在 {region}, 返回 {page_size} 条")
        try:
            result = place_search(query, region, page_size)
            print(f"结果:\n{result}")
        except Exception as e:
            print(f"错误: {e}")


def test_get_direction():
    """测试路线规划功能"""
    print("\n" + "=" * 60)
    print("测试 4: 路线规划 (get_direction)")
    print("=" * 60)

    test_cases = [
        ("北京天安门", "北京故宫", "driving"),
        ("上海外滩", "东方明珠", "transit"),
    ]

    for origin, destination, mode in test_cases:
        print(f"\n路线: {origin} -> {destination}, 方式: {mode}")
        try:
            result = get_direction(origin, destination, mode)
            print(f"结果:\n{result}")
        except Exception as e:
            print(f"错误: {e}")


def test_get_ip_location():
    """测试IP定位功能"""
    print("\n" + "=" * 60)
    print("测试 5: IP定位 (get_ip_location)")
    print("=" * 60)

    try:
        result = get_ip_location()
        print(f"结果:\n{result}")
    except Exception as e:
        print(f"错误: {e}")


async def test_mcp_tools():
    """通过MCP协议测试工具调用"""
    print("\n" + "=" * 60)
    print("测试 6: MCP协议工具调用测试")
    print("=" * 60)

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langchain_mcp_adapters.tools import load_mcp_tools

        server_config = {
            "map": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [__file__.replace("test_map.py", "server.py")],
            },
        }

        print("\n连接MCP服务器...")
        client = MultiServerMCPClient(server_config)

        async with client.session("map") as session:
            tools = await load_mcp_tools(session)
            print(f"成功加载 {len(tools)} 个工具")

            for tool in tools:
                print(f"\n  - {tool.name}")
                print(f"    描述: {tool.description[:80]}...")

                # 测试调用每个工具
                if tool.name == "geocode":
                    print("    测试调用: geocode('北京市天安门')")
                    result = await tool.ainvoke({"address": "北京市天安门"})
                    print(f"    结果: {result[:100]}...")

    except Exception as e:
        print(f"MCP测试失败: {e}")
        import traceback

        traceback.print_exc()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("百度地图MCP服务测试")
    print("=" * 60)

    # 检查环境变量
    if not os.getenv("BAIDU_MAP_AK"):
        print("\n⚠️  警告: 未设置 BAIDU_MAP_AK 环境变量")
        print("   测试将显示错误信息\n")

    # 运行基础功能测试
    test_geocode()
    test_reverse_geocode()
    test_place_search()
    test_get_direction()
    test_get_ip_location()

    # 运行MCP协议测试
    print("\n运行MCP协议测试...")
    asyncio.run(test_mcp_tools())

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
