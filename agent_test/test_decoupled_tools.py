# -*- coding: utf-8 -*-
"""
测试 decoupled_agent 中的工具调用
"""

import sys
import asyncio
from pathlib import Path

# 添加父目录到路径
agent_root = Path(__file__).parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

print("=" * 80)
print("测试 decoupled_agent 工具调用")
print("=" * 80)

# 1. 先加载环境变量
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"\n[OK] 已加载环境变量: {env_path}")

# 2. 导入 decoupled_agent 的组件
print("\n[1] 导入组件...")
try:
    from decoupled_agent import (
        ToolExecutor,
        IntentClassifier,
        DecoupledAgent,
        MessageBuilder,
        PerformanceMetrics,
        IntentType,
        ALL_FUNCTIONS,
        ALL_TOOLS,
    )

    print(f"  [OK] 成功导入")
    print(f"  可用函数: {len(ALL_FUNCTIONS)} 个")
    print(f"  可用工具: {len(ALL_TOOLS)} 个")
except Exception as e:
    print(f"  [ERROR] 导入失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# 3. 测试 ToolExecutor 直接调用
print("\n[2] 测试 ToolExecutor 直接调用...")

tool_executor = ToolExecutor(ALL_FUNCTIONS)


async def test_tool_executor():
    # 测试 1: get_weather_now
    print("\n  测试 1: get_weather_now('北京')")
    try:
        result = await tool_executor.execute("get_weather_now", {"location": "北京"})
        print(f"    [OK] 执行成功!")
        print(f"    工具名: {result.tool_name}")
        print(f"    参数: {result.arguments}")
        print(f"    耗时: {result.duration_ms:.2f} ms")
        if result.result.startswith("[ERROR]"):
            print(f"    [ERROR] 结果包含错误: {result.result}")
        else:
            print(f"    结果前50字符: {result.result[:50]}...")
    except Exception as e:
        print(f"    [ERROR] 执行异常: {e}")
        import traceback

        traceback.print_exc()

    # 测试 2: 使用空参数字典
    print("\n  测试 2: get_weather_now({}) [空参数]")
    try:
        result = await tool_executor.execute("get_weather_now", {})
        print(f"    结果: {result.result[:100]}")
    except Exception as e:
        print(f"    [ERROR] 执行异常: {e}")

    # 测试 3: 使用错误的参数名
    print("\n  测试 3: get_weather_now({'city': '北京'}) [错误参数名]")
    try:
        result = await tool_executor.execute("get_weather_now", {"city": "北京"})
        print(f"    结果: {result.result[:100]}")
    except Exception as e:
        print(f"    [ERROR] 执行异常: {e}")

    # 测试 4: geocode
    print("\n  测试 4: geocode({'address': '北京天安门'})")
    try:
        result = await tool_executor.execute("geocode", {"address": "北京天安门"})
        print(f"    [OK] 执行成功!")
        print(f"    耗时: {result.duration_ms:.2f} ms")
        if result.result.startswith("[ERROR]"):
            print(f"    [ERROR] 结果包含错误: {result.result}")
        else:
            print(f"    结果前50字符: {result.result[:50]}...")
    except Exception as e:
        print(f"    [ERROR] 执行异常: {e}")
        import traceback

        traceback.print_exc()


asyncio.run(test_tool_executor())

# 4. 测试批量执行
print("\n[3] 测试批量工具执行...")


async def test_batch_execution():
    tool_calls = [
        {"name": "get_weather_now", "arguments": {"location": "上海"}},
        {"name": "geocode", "arguments": {"address": "上海外滩"}},
    ]

    try:
        results = await tool_executor.execute_multiple(tool_calls)
        print(f"  [OK] 批量执行完成，共 {len(results)} 个结果")
        for i, result in enumerate(results):
            print(f"\n  结果 {i + 1}:")
            print(f"    工具: {result.tool_name}")
            print(f"    耗时: {result.duration_ms:.2f} ms")
            if result.result.startswith("[ERROR]"):
                print(f"    [ERROR] {result.result}")
            else:
                print(f"    结果: {result.result[:60]}...")
    except Exception as e:
        print(f"  [ERROR] 批量执行失败: {e}")
        import traceback

        traceback.print_exc()


asyncio.run(test_batch_execution())

# 5. 检查可能的错误场景
print("\n[4] 常见错误场景检查...")

# 检查 1: HEFENG_KEY 是否正确加载
import os

hefeng_key = os.getenv("HEFENG_KEY")
if not hefeng_key:
    print("  [WARNING] HEFENG_KEY 环境变量未设置!")
    print("  这会导致所有天气工具返回: '错误：未配置和风天气KEY密钥'")
else:
    print(f"  [OK] HEFENG_KEY 已设置 (长度: {len(hefeng_key)})")

# 检查 2: BAIDU_MAP_AK 是否正确加载
baidu_ak = os.getenv("BAIDU_MAP_AK")
if not baidu_ak:
    print("  [WARNING] BAIDU_MAP_AK 环境变量未设置!")
    print("  这会导致所有地图工具返回: '错误：未配置百度地图AK密钥'")
else:
    print(f"  [OK] BAIDU_MAP_AK 已设置 (长度: {len(baidu_ak)})")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
print("\n如果看到 '[ERROR]' 结果，请检查:")
print("  1. .env 文件是否正确配置了 API keys")
print("  2. API keys 是否有效")
print("  3. 网络连接是否正常")
