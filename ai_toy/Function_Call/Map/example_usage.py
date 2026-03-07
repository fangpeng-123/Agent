# -*- coding: utf-8 -*-
"""
百度地图Function Call工具使用示例
演示如何在LLM Function Call场景中使用地图工具
"""

import json
from map_tools import MAP_TOOLS, MAP_FUNCTIONS


def example_usage_with_openai():
    """
    示例：与OpenAI API集成使用
    """
    print("=" * 60)
    print("示例：与OpenAI API集成使用")
    print("=" * 60)

    print("\n工具定义示例：")
    print(json.dumps(MAP_TOOLS[0], indent=2, ensure_ascii=False))

    print("\n函数调用示例：")
    print("function_name: geocode")
    print('arguments: {"address": "北京市天安门"}')
    print("\n调用结果：")
    result = MAP_FUNCTIONS["geocode"]("北京市天安门")
    print(result)


def example_direct_usage():
    """
    示例：直接调用函数
    """
    print("\n" + "=" * 60)
    print("示例：直接调用函数")
    print("=" * 60)

    # 地理编码
    print("\n1. 地理编码（地址转坐标）：")
    result = geocode("北京市故宫")
    print(result)

    # 逆地理编码
    print("\n2. 逆地理编码（坐标转地址）：")
    result = reverse_geocode(39.9163, 116.3972)
    print(result[:300] + "..." if len(result) > 300 else result)

    # 地点搜索
    print("\n3. 地点搜索：")
    result = place_search("火锅", region="北京", page_size=3)
    print(result)

    # 路线规划
    print("\n4. 路线规划：")
    result = get_direction("北京天安门", "北京故宫", mode="walking")
    print(result[:400] + "..." if len(result) > 400 else result)


def example_with_langchain():
    """
    示例：与LangChain集成使用
    """
    print("\n" + "=" * 60)
    print("示例：与LangChain集成使用")
    print("=" * 60)

    print("""
# 使用方式：
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from map_tools import MAP_FUNCTIONS

# 创建工具列表
tools = [
    Tool(
        name="geocode",
        func=MAP_FUNCTIONS["geocode"],
        description="将地址转换为经纬度坐标"
    ),
    Tool(
        name="place_search",
        func=MAP_FUNCTIONS["place_search"],
        description="搜索POI地点"
    ),
    Tool(
        name="get_direction",
        func=MAP_FUNCTIONS["get_direction"],
        description="获取两地之间的路线规划"
    ),
    # ... 其他工具
]

# 初始化Agent
llm = ChatOpenAI(model="gpt-4")
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="openai-functions",
    verbose=True
)

# 使用Agent
result = agent.run("从天安门到故宫怎么走？")
print(result)
""")


if __name__ == "__main__":
    # 导入函数
    from map_tools import (
        geocode,
        reverse_geocode,
        place_search,
        get_direction,
        get_ip_location,
    )

    print("[INFO] 百度地图Function Call工具使用示例")
    print("-" * 60)

    # 运行示例
    example_usage_with_openai()
    example_direct_usage()
    example_with_langchain()

    print("\n" + "=" * 60)
    print("[OK] 示例运行完成")
    print("=" * 60)
