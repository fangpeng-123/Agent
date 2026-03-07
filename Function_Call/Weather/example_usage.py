# -*- coding: utf-8 -*-
"""
和风天气Function Call工具使用示例
演示如何在LLM Function Call场景中使用天气工具
"""

import json
from weather_tools import WEATHER_TOOLS, WEATHER_FUNCTIONS


def example_usage_with_openai():
    """
    示例：与OpenAI API集成使用
    """
    print("=" * 60)
    print("示例：与OpenAI API集成使用")
    print("=" * 60)

    # 假设你已经有一个OpenAI客户端
    # from openai import OpenAI
    # client = OpenAI(api_key="your-api-key")

    # 1. 将工具定义传递给LLM
    # response = client.chat.completions.create(
    #     model="gpt-4",
    #     messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
    #     tools=WEATHER_TOOLS,  # 传入工具定义
    #     tool_choice="auto"
    # )

    # 2. 检查LLM是否请求调用工具
    # if response.choices[0].message.tool_calls:
    #     tool_call = response.choices[0].message.tool_calls[0]
    #     function_name = tool_call.function.name
    #     arguments = json.loads(tool_call.function.arguments)
    #
    #     # 3. 调用对应的函数
    #     if function_name in WEATHER_FUNCTIONS:
    #         result = WEATHER_FUNCTIONS[function_name](**arguments)
    #         print(result)

    print("\n工具定义示例：")
    print(json.dumps(WEATHER_TOOLS[0], indent=2, ensure_ascii=False))

    print("\n函数调用示例：")
    print("function_name: get_weather_now")
    print('arguments: {"location": "北京"}')
    print("\n调用结果：")
    result = WEATHER_FUNCTIONS["get_weather_now"]("北京")
    print(result)


def example_direct_usage():
    """
    示例：直接调用函数
    """
    print("\n" + "=" * 60)
    print("示例：直接调用函数")
    print("=" * 60)

    # 获取实时天气
    print("\n1. 获取实时天气：")
    result = get_weather_now("上海")
    print(result)

    # 获取天气预报
    print("\n2. 获取7天天气预报：")
    result = get_weather_forecast("广州", days=7)
    print(result[:500] + "..." if len(result) > 500 else result)

    # 获取空气质量
    print("\n3. 获取空气质量：")
    result = get_air_quality("深圳")
    print(result)

    # 获取生活指数
    print("\n4. 获取生活指数：")
    result = get_life_index("杭州")
    print(result[:500] + "..." if len(result) > 500 else result)


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
from weather_tools import WEATHER_FUNCTIONS

# 创建工具列表
tools = [
    Tool(
        name="get_weather_now",
        func=WEATHER_FUNCTIONS["get_weather_now"],
        description="获取指定城市的实时天气情况"
    ),
    Tool(
        name="get_weather_forecast",
        func=WEATHER_FUNCTIONS["get_weather_forecast"],
        description="获取指定城市的未来天气预报"
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
result = agent.run("北京今天天气怎么样？")
print(result)
""")


if __name__ == "__main__":
    # 导入函数
    from weather_tools import (
        get_weather_now,
        get_weather_forecast,
        get_air_quality,
        get_life_index,
    )

    print("[INFO] 和风天气Function Call工具使用示例")
    print("-" * 60)

    # 运行示例
    example_usage_with_openai()
    example_direct_usage()
    example_with_langchain()

    print("\n" + "=" * 60)
    print("[OK] 示例运行完成")
    print("=" * 60)
