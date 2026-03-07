# -*- coding: utf-8 -*-
"""
整合Function Call工具示例
演示如何同时使用天气和地图工具构建智能Agent
"""

import sys
import os
from pathlib import Path

# 添加工具目录到路径
sys.path.append(str(Path(__file__).parent / "Weather"))
sys.path.append(str(Path(__file__).parent / "Map"))

from weather_tools import WEATHER_TOOLS, WEATHER_FUNCTIONS
from map_tools import MAP_TOOLS, MAP_FUNCTIONS


class FunctionCallAgent:
    """
    Function Call Agent示例
    模拟LLM Function Call的工作流程
    """

    def __init__(self):
        # 合并所有工具
        self.all_tools = WEATHER_TOOLS + MAP_TOOLS
        self.all_functions = {**WEATHER_FUNCTIONS, **MAP_FUNCTIONS}

        print(f"[OK] 已加载 {len(self.all_tools)} 个工具")
        print(f"   - 天气工具: {len(WEATHER_TOOLS)} 个")
        print(f"   - 地图工具: {len(MAP_TOOLS)} 个")

    def get_tools(self):
        """获取所有工具定义（用于传递给LLM）"""
        return self.all_tools

    def get_function(self, name: str):
        """根据名称获取函数"""
        return self.all_functions.get(name)

    def execute_tool(self, function_name: str, arguments: dict) -> str:
        """
        执行工具调用

        Args:
            function_name: 函数名称
            arguments: 参数字典

        Returns:
            工具执行结果
        """
        func = self.get_function(function_name)
        if func:
            try:
                return func(**arguments)
            except Exception as e:
                return f"[ERROR] 执行失败: {str(e)}"
        else:
            return f"[ERROR] 未找到工具: {function_name}"

    def list_tools(self):
        """列出所有可用工具"""
        print("\n可用工具列表：")
        print("-" * 60)
        print("\n天气工具：")
        for tool in WEATHER_TOOLS:
            name = tool["function"]["name"]
            desc = tool["function"]["description"][:50]
            print(f"  - {name}: {desc}...")

        print("\n地图工具：")
        for tool in MAP_TOOLS:
            name = tool["function"]["name"]
            desc = tool["function"]["description"][:50]
            print(f"  - {name}: {desc}...")


def simulate_llm_function_call():
    """
    模拟LLM Function Call流程
    """
    print("=" * 60)
    print("模拟LLM Function Call流程")
    print("=" * 60)

    agent = FunctionCallAgent()

    # 示例1: 天气查询
    print("\n" + "-" * 60)
    print("场景1: 用户询问天气")
    print("-" * 60)
    print("用户: 北京今天天气怎么样？")
    print("\nLLM识别到需要调用工具:")
    print("  tool: get_weather_now")
    print("  arguments: {'location': '北京'}")

    result = agent.execute_tool("get_weather_now", {"location": "北京"})
    print("\n工具执行结果：")
    print(result)

    # 示例2: 地理编码
    print("\n" + "-" * 60)
    print("场景2: 用户询问地址坐标")
    print("-" * 60)
    print("用户: 北京市天安门广场的经纬度是多少？")
    print("\nLLM识别到需要调用工具:")
    print("  tool: geocode")
    print("  arguments: {'address': '北京市天安门广场'}")

    result = agent.execute_tool("geocode", {"address": "北京市天安门广场"})
    print("\n工具执行结果：")
    print(result)

    # 示例3: 路线规划
    print("\n" + "-" * 60)
    print("场景3: 用户询问路线")
    print("-" * 60)
    print("用户: 从天安门到故宫怎么走？")
    print("\nLLM识别到需要调用工具:")
    print("  tool: get_direction")
    print("  arguments: {'origin': '天安门', 'destination': '故宫', 'mode': 'walking'}")

    result = agent.execute_tool(
        "get_direction", {"origin": "天安门", "destination": "故宫", "mode": "walking"}
    )
    print("\n工具执行结果：")
    print(result[:400] + "..." if len(result) > 400 else result)

    # 示例4: 地点搜索
    print("\n" + "-" * 60)
    print("场景4: 用户搜索地点")
    print("-" * 60)
    print("用户: 北京有哪些好吃的火锅店？")
    print("\nLLM识别到需要调用工具:")
    print("  tool: place_search")
    print("  arguments: {'query': '火锅', 'region': '北京', 'page_size': 5}")

    result = agent.execute_tool(
        "place_search", {"query": "火锅", "region": "北京", "page_size": 5}
    )
    print("\n工具执行结果：")
    print(result)


def demo_with_openai_format():
    """
    演示OpenAI格式的工具调用
    """
    print("\n" + "=" * 60)
    print("OpenAI格式工具定义示例")
    print("=" * 60)

    agent = FunctionCallAgent()
    tools = agent.get_tools()

    print("\n工具定义JSON格式（可直接用于OpenAI API）：")
    import json

    print(json.dumps(tools[0], indent=2, ensure_ascii=False))

    print("\n" + "-" * 60)
    print("在实际使用中的代码示例：")
    print("-" * 60)
    print("""
from openai import OpenAI
import json

client = OpenAI(api_key="your-api-key")

# 1. 发送消息和工具定义给LLM
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "北京今天天气怎么样？"}
    ],
    tools=agent.get_tools(),  # 传入所有工具定义
    tool_choice="auto"
)

# 2. 检查LLM是否需要调用工具
message = response.choices[0].message
if message.tool_calls:
    # LLM要求调用工具
    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    # 3. 执行工具调用
    result = agent.execute_tool(function_name, arguments)
    
    # 4. 将结果返回给LLM
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "北京今天天气怎么样？"},
            message,  # 包含工具调用请求
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            }
        ]
    )
    
    print(response.choices[0].message.content)
""")


if __name__ == "__main__":
    print("[INFO] Function Call Agent示例")
    print()

    # 模拟LLM Function Call
    simulate_llm_function_call()

    # 展示工具定义格式
    demo_with_openai_format()

    print("\n" + "=" * 60)
    print("[OK] 所有示例运行完成")
    print("=" * 60)
