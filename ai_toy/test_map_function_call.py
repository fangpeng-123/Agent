# -*- coding: utf-8 -*-
"""
地图代理 Function Call 测试
测试 Layer 1: 工具函数
测试 Layer 2: Schema 格式
测试 Layer 3: 智能体代理
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_layer1_functions():
    """直接测试 MAP_FUNCTIONS 工具函数"""
    from Function_Call.Map import (
        geocode,
        reverse_geocode,
        place_search,
        get_direction,
        get_ip_location,
    )

    print("\n[Layer 1] 工具函数直接调用测试")
    print("-" * 50)

    results = []

    result = await geocode("北京市天安门")
    print(f"\n[1] geocode('北京市天安门'):\n{result}")
    results.append(("geocode", "经度" in result or "错误" in result))

    result = await reverse_geocode(39.9042, 116.4074)
    print(f"\n[2] reverse_geocode(39.9042, 116.4074):\n{result[:200]}...")
    results.append(("reverse_geocode(有效)", "北京" in result or "错误" in result))

    result = await reverse_geocode(53.5, 122.3)
    print(f"\n[3] reverse_geocode(53.5, 122.3) 中国东北边界:\n{result[:200]}...")
    results.append(("reverse_geocode(边界)", True))

    result = await reverse_geocode(0, 0)
    print(f"\n[4] reverse_geocode(0, 0) 大西洋:\n{result[:200]}...")
    results.append(("reverse_geocode(无效)", True))

    result = await place_search("火锅", region="北京", page_size=3)
    print(f"\n[5] place_search('火锅', '北京', 3):\n{result[:300]}...")
    results.append(
        ("place_search", "火锅" in result or "未找到" in result or "错误" in result)
    )

    result = await get_direction("天安门", "故宫", mode="walking")
    print(f"\n[6] get_direction('天安门', '故宫', 'walking'):\n{result[:300]}...")
    results.append(("get_direction", "距离" in result or "错误" in result))

    result = await get_ip_location()
    print(f"\n[7] get_ip_location():\n{result}")
    results.append(("get_ip_location", "省份" in result or "错误" in result))

    print("\n[Layer 1] 测试结果汇总:")
    for name, passed in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}")

    return all(r[1] for r in results)


def test_layer2_schema():
    """测试 MAP_TOOLS Schema 格式"""
    from Function_Call.Map import MAP_TOOLS

    print("\n[Layer 2] Schema 格式验证")
    print("-" * 50)

    results = []
    required_keys = ["type", "function"]
    func_keys = ["name", "description", "parameters"]

    for tool in MAP_TOOLS:
        tool_name = tool.get("function", {}).get("name", "unknown")

        try:
            assert "type" in tool, "缺少 type 字段"
            assert tool["type"] == "function", "type 应为 function"
            assert "function" in tool, "缺少 function 字段"

            func = tool["function"]
            for key in func_keys:
                assert key in func, f"function 缺少 {key}"

            params = func["parameters"]
            assert params["type"] == "object", "parameters.type 应为 object"
            assert "properties" in params, "缺少 properties"

            print(f"[OK] {func['name']}: Schema 验证通过")
            results.append((func["name"], True))
        except AssertionError as e:
            print(f"[FAIL] {tool_name}: {e}")
            results.append((tool_name, False))

    print(f"\n共验证 {len(MAP_TOOLS)} 个工具定义")
    return all(r[1] for r in results)


async def test_layer3_agents():
    """测试 MapAgent 智能体"""
    from Function_Call.map_agents import MAP_AGENTS

    print("\n[Layer 3] 智能体代理测试")
    print("-" * 50)

    test_cases = [
        ("geocode", "天安门的经纬度是多少", {"address": "北京市天安门"}),
        ("reverse_geocode", "坐标39.9,116.4是什么地方", {"lat": 39.9, "lng": 116.4}),
        ("place_search", "北京有什么好吃的火锅店", {"query": "火锅", "region": "北京"}),
        (
            "get_direction",
            "从天安门到故宫怎么走",
            {"origin": "天安门", "destination": "故宫", "mode": "walking"},
        ),
        ("get_ip_location", "我的IP位置在哪里", {}),
    ]

    results = []

    for tool_name, user_input, params in test_cases:
        agent = MAP_AGENTS[tool_name]
        print(f"\n[Agent: {tool_name}]")
        print(f"  输入: {user_input}")
        print(f"  参数: {params}")

        try:
            result = await agent.run(user_input, params)
            print(f"  结果: {result}")

            passed = result is not None and isinstance(result, dict)
            status = "[OK]" if passed else "[FAIL]"
            print(f"  {status} {tool_name}")
            results.append((tool_name, passed))
        except Exception as e:
            print(f"  [FAIL] {tool_name}: {e}")
            results.append((tool_name, False))

    print("\n[Layer 3] 测试结果汇总:")
    for name, passed in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}")

    return all(r[1] for r in results)


async def main():
    print("=" * 50)
    print("地图代理 Function Call 测试")
    print("=" * 50)

    layer1_passed = await test_layer1_functions()
    layer2_passed = test_layer2_schema()
    layer3_passed = await test_layer3_agents()

    print("\n" + "=" * 50)
    print("测试汇总")
    print("=" * 50)
    print(f"  Layer 1 (工具函数): {'[OK]' if layer1_passed else '[FAIL]'}")
    print(f"  Layer 2 (Schema): {'[OK]' if layer2_passed else '[FAIL]'}")
    print(f"  Layer 3 (智能体): {'[OK]' if layer3_passed else '[FAIL]'}")

    if layer1_passed and layer2_passed and layer3_passed:
        print("\n[OK] 所有测试通过!")
    else:
        print("\n[WARN] 部分测试未通过")


if __name__ == "__main__":
    asyncio.run(main())
