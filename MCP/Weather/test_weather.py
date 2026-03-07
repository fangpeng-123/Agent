# -*- coding: utf-8 -*-
"""
和风天气MCP服务测试
测试各个工具是否能正常调用
"""

import asyncio
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import (
    mcp,
    _get_weather_now as get_weather_now,
    _get_weather_forecast as get_weather_forecast,
    _get_hourly_forecast as get_hourly_forecast,
    _get_air_quality as get_air_quality,
    _get_life_index as get_life_index,
    _search_city as search_city,
)


def test_get_weather_now():
    """测试实时天气查询"""
    print("\n" + "=" * 60)
    print("测试 1: 实时天气 (get_weather_now)")
    print("=" * 60)

    test_cases = ["北京", "上海", "101010100"]  # 城市名和城市ID

    for location in test_cases:
        print(f"\n查询城市: {location}")
        try:
            result = get_weather_now(location)
            print(f"结果:\n{result}")
        except Exception as e:
            print(f"错误: {e}")


def test_get_weather_forecast():
    """测试天气预报查询"""
    print("\n" + "=" * 60)
    print("测试 2: 天气预报 (get_weather_forecast)")
    print("=" * 60)

    test_cases = [
        ("北京", 3),
        ("上海", 7),
    ]

    for location, days in test_cases:
        print(f"\n查询城市: {location}, 天数: {days}")
        try:
            result = get_weather_forecast(location, days)
            print(f"结果:\n{result}")
        except Exception as e:
            print(f"错误: {e}")


def test_get_hourly_forecast():
    """测试逐小时天气预报"""
    print("\n" + "=" * 60)
    print("测试 3: 逐小时预报 (get_hourly_forecast)")
    print("=" * 60)

    test_cases = [
        ("北京", 24),
        ("上海", 24),
    ]

    for location, hours in test_cases:
        print(f"\n查询城市: {location}, 小时数: {hours}")
        try:
            result = get_hourly_forecast(location, hours)
            print(f"结果:\n{result}")
        except Exception as e:
            print(f"错误: {e}")


def test_get_air_quality():
    """测试空气质量查询"""
    print("\n" + "=" * 60)
    print("测试 4: 空气质量 (get_air_quality)")
    print("=" * 60)

    test_cases = ["北京", "上海"]

    for location in test_cases:
        print(f"\n查询城市: {location}")
        try:
            result = get_air_quality(location)
            print(f"结果:\n{result}")
        except Exception as e:
            print(f"错误: {e}")


def test_get_life_index():
    """测试生活指数查询"""
    print("\n" + "=" * 60)
    print("测试 5: 生活指数 (get_life_index)")
    print("=" * 60)

    test_cases = ["北京", "上海"]

    for location in test_cases:
        print(f"\n查询城市: {location}")
        try:
            result = get_life_index(location)
            print(f"结果:\n{result}")
        except Exception as e:
            print(f"错误: {e}")


def test_search_city():
    """测试城市搜索"""
    print("\n" + "=" * 60)
    print("测试 6: 城市搜索 (search_city)")
    print("=" * 60)

    test_cases = ["北京", "上海", "广州"]

    for city_name in test_cases:
        print(f"\n搜索城市: {city_name}")
        try:
            result = search_city(city_name)
            print(f"结果:\n{result}")
        except Exception as e:
            print(f"错误: {e}")


async def test_mcp_tools():
    """通过MCP协议测试工具调用"""
    print("\n" + "=" * 60)
    print("测试 7: MCP协议工具调用测试")
    print("=" * 60)

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langchain_mcp_adapters.tools import load_mcp_tools

        server_config = {
            "weather": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [__file__.replace("test_weather.py", "server.py")],
            },
        }

        print("\n连接MCP服务器...")
        client = MultiServerMCPClient(server_config)

        async with client.session("weather") as session:
            tools = await load_mcp_tools(session)
            print(f"成功加载 {len(tools)} 个工具")

            for tool in tools:
                print(f"\n  - {tool.name}")
                print(f"    描述: {tool.description[:80]}...")

                # 测试调用实时天气工具
                if tool.name == "get_weather_now":
                    print("    测试调用: get_weather_now('北京')")
                    result = await tool.ainvoke({"location": "北京"})
                    print(f"    结果: {result[:150]}...")

    except Exception as e:
        print(f"MCP测试失败: {e}")
        import traceback

        traceback.print_exc()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("和风天气MCP服务测试")
    print("=" * 60)

    # 检查环境变量
    if not os.getenv("HEFENG_KEY"):
        print("\n⚠️  警告: 未设置 HEFENG_KEY 环境变量")
        print("   测试将显示错误信息\n")

    # 运行基础功能测试
    test_get_weather_now()
    test_get_weather_forecast()
    test_get_hourly_forecast()
    test_get_air_quality()
    test_get_life_index()
    test_search_city()

    # 运行MCP协议测试
    print("\n运行MCP协议测试...")
    asyncio.run(test_mcp_tools())

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
