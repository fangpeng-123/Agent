# -*- coding: utf-8 -*-
"""
测试 Function_Call 模块导入
"""

import sys
from pathlib import Path

# 添加父目录到路径
agent_root = Path(__file__).parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

print(f"Python 版本: {sys.version}")
print(f"\n尝试导入路径: {agent_root}")
print(f"\nsys.path 前3项:")
for i, p in enumerate(sys.path[:3]):
    print(f"  [{i}] {p}")

print("\n" + "=" * 60)
print("开始导入测试...")
print("=" * 60)

try:
    # 方法1: 从 Function_Call 包导入
    print("\n方法1: from Function_Call import ALL_TOOLS, ALL_FUNCTIONS")
    from Function_Call import ALL_TOOLS, ALL_FUNCTIONS

    print(f"[OK] 成功导入!")
    print(f"     ALL_TOOLS 数量: {len(ALL_TOOLS)}")
    print(f"     ALL_FUNCTIONS 数量: {len(ALL_FUNCTIONS)}")

    # 显示工具列表
    print("\n可用工具:")
    for tool in ALL_TOOLS:
        name = tool["function"]["name"]
        desc = tool["function"]["description"][:30]
        print(f"  - {name}: {desc}...")

    # 测试调用一个工具
    print("\n测试调用工具: get_weather_now")
    if "get_weather_now" in ALL_FUNCTIONS:
        # 注意：这需要一个有效的 API key，这里只测试函数存在性
        print(f"[OK] 工具函数存在: {ALL_FUNCTIONS['get_weather_now']}")

except ImportError as e:
    print(f"[ERROR] 导入失败: {e}")
    import traceback

    traceback.print_exc()

try:
    # 方法2: 单独导入子模块
    print("\n" + "-" * 60)
    print("方法2: 从子模块导入")
    from Function_Call.Weather import WEATHER_TOOLS, WEATHER_FUNCTIONS
    from Function_Call.Map import MAP_TOOLS, MAP_FUNCTIONS

    print(f"[OK] Weather 工具: {len(WEATHER_TOOLS)} 个")
    print(f"[OK] Map 工具: {len(MAP_TOOLS)} 个")

except ImportError as e:
    print(f"[ERROR] 子模块导入失败: {e}")

print("\n" + "=" * 60)
print("导入测试完成!")
print("=" * 60)
