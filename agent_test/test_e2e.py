# -*- coding: utf-8 -*-
"""
端到端测试 - 验证完整的解耦智能体流程
使用模拟模型避免依赖真实 API
"""

import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

agent_root = Path(__file__).parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

print("=" * 80)
print("端到端测试 - 解耦智能体")
print("=" * 80)

from decoupled_agent import DecoupledAgent, IntentType, ALL_FUNCTIONS, MessageBuilder


# 创建模拟模型
class MockIntentModel:
    """模拟意图分类模型"""

    async def ainvoke(self, messages):
        # 根据用户输入返回不同的意图
        user_msg = messages[-1]["content"] if messages else ""

        if "天气" in user_msg:
            return MagicMock(
                content="""{
                "intent": "tool_call",
                "confidence": 0.95,
                "reasoning": "用户询问天气",
                "suggested_tools": ["get_weather_now"],
                "extracted_params": {"location": "北京"}
            }"""
            )
        elif "路线" in user_msg or "怎么走" in user_msg:
            return MagicMock(
                content="""{
                "intent": "tool_call",
                "confidence": 0.92,
                "reasoning": "用户询问路线",
                "suggested_tools": ["get_direction"],
                "extracted_params": {"origin": "天安门", "destination": "故宫", "mode": "walking"}
            }"""
            )
        else:
            return MagicMock(
                content="""{
                "intent": "direct_chat",
                "confidence": 0.98,
                "reasoning": "用户闲聊",
                "suggested_tools": [],
                "extracted_params": {}
            }"""
            )

    def astream(self, messages):
        pass


class MockMainModel:
    """模拟主模型"""

    async def ainvoke(self, messages):
        # 根据消息内容生成回复
        last_msg = messages[-1]["content"] if messages else ""

        if "工具调用结果" in last_msg and "天气" in last_msg:
            return MagicMock(
                content="根据查询结果，北京今天天气晴朗，温度适宜，非常适合外出！"
            )
        elif "工具调用结果" in last_msg and "路线" in last_msg:
            return MagicMock(
                content="从天安门到故宫大约需要15分钟步行，推荐走南池子大街。"
            )
        else:
            return MagicMock(content="我理解你的问题，这是一个很有趣的话题！")

    async def astream(self, messages):
        # 模拟流式输出
        last_msg = messages[-1]["content"] if messages else ""

        if "工具调用结果" in last_msg:
            words = ["根据", "查询", "结果", "，", "这里", "是", "回复", "。"]
        else:
            words = ["这是", "直接", "对话", "的", "回复", "。"]

        for word in words:
            yield MagicMock(content=word)


async def test_full_workflow():
    """测试完整工作流"""

    # 1. 初始化 Agent
    print("\n[1] 初始化 Agent...")
    intent_model = MockIntentModel()
    main_model = MockMainModel()

    agent = DecoupledAgent(
        intent_model=intent_model,
        main_model=main_model,
        tools=ALL_FUNCTIONS,  # 使用真实的工具函数
    )
    print("  [OK] Agent 初始化完成")

    # 2. 测试用例
    test_cases = [
        {
            "name": "闲聊（直接对话）",
            "input": "你好，很高兴见到你！",
            "expected_intent": IntentType.DIRECT_CHAT,
        },
        {
            "name": "天气查询（工具调用）",
            "input": "北京今天天气怎么样？",
            "expected_intent": IntentType.TOOL_CALL,
        },
        {
            "name": "路线查询（工具调用）",
            "input": "从天安门到故宫怎么走？",
            "expected_intent": IntentType.TOOL_CALL,
        },
    ]

    # 3. 执行测试
    print("\n[2] 执行测试用例...")
    for i, test in enumerate(test_cases, 1):
        print(f"\n  测试 {i}/{len(test_cases)}: {test['name']}")
        print(f"  用户输入: {test['input']}")
        print(f"  期望意图: {test['expected_intent'].value}")

        try:
            # 执行处理
            response = await agent.process(test["input"], stream=False)

            print(f"  实际意图: {response.intent.value}")
            print(f"  置信度: {response.intent == test['expected_intent']}")
            print(f"  AI回复: {response.content[:50]}...")

            if response.tool_calls:
                print(f"  工具调用: {len(response.tool_calls)} 个")
                for tc in response.tool_calls:
                    print(f"    - {tc.tool_name}: {tc.duration_ms:.2f}ms")

            # 验证意图
            if response.intent == test["expected_intent"]:
                print(f"  [PASS] 意图匹配")
            else:
                print(f"  [FAIL] 意图不匹配")

            # 打印性能报告
            if response.metrics:
                print(
                    f"  总耗时: {sum(response.metrics.stage_durations.values()):.2f}ms"
                )

        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

    # 4. 验证对话历史
    print("\n[3] 验证对话历史...")
    print(f"  历史消息数: {len(agent.conversation_history)}")
    print("  消息角色序列:")
    for i, msg in enumerate(agent.conversation_history):
        role = msg["role"]
        content_preview = (
            msg.get("content", "")[:30] + "..."
            if len(msg.get("content", "")) > 30
            else msg.get("content", "")
        )
        print(f"    [{i}] {role}: {content_preview}")

    # 验证没有 tool 消息
    tool_msgs = [msg for msg in agent.conversation_history if msg.get("role") == "tool"]
    if tool_msgs:
        print(f"  [WARNING] 发现 {len(tool_msgs)} 条 tool 消息")
    else:
        print(f"  [OK] 历史中没有 tool 消息（符合预期）")

    # 5. 验证消息格式（模拟 OpenAI API 验证）
    print("\n[4] 验证 OpenAI API 消息格式...")

    def validate_messages(messages):
        """验证消息格式"""
        errors = []
        for i, msg in enumerate(messages):
            if msg.get("role") == "tool":
                if i == 0:
                    errors.append(f"消息{i}: tool消息不能是第一个")
                else:
                    prev = messages[i - 1]
                    if prev.get("role") != "assistant":
                        errors.append(f"消息{i}: tool消息前必须是assistant")
                    elif "tool_calls" not in prev:
                        errors.append(f"消息{i}: 前一个assistant缺少tool_calls")
        return errors

    # 构建完整消息列表
    full_messages = MessageBuilder.build_main_model_messages(
        "测试消息", [], agent.conversation_history
    )

    errors = validate_messages(full_messages)
    if errors:
        print(f"  [ERROR] 格式错误:")
        for err in errors:
            print(f"    - {err}")
    else:
        print(f"  [OK] 消息格式符合 OpenAI API 要求")

    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


# 运行测试
if __name__ == "__main__":
    asyncio.run(test_full_workflow())
