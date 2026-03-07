# -*- coding: utf-8 -*-
"""
验证 OpenAI API 消息格式修复
"""

import sys
from pathlib import Path

agent_root = Path(__file__).parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

print("=" * 80)
print("验证 OpenAI API 消息格式")
print("=" * 80)

# 1. 测试消息构建
print("\n[1] 测试 MessageBuilder")
from decoupled_agent import MessageBuilder, ToolCall

# 创建模拟工具调用
mock_tool_calls = [
    ToolCall(
        tool_name="get_weather_now",
        arguments={"location": "北京"},
        result="[位置] 北京 实时天气\n[温度] 25°C...",
        start_time=0,
        end_time=0.5,
    )
]

# 测试消息构建
messages = MessageBuilder.build_main_model_messages(
    user_input="北京天气怎么样？", tool_results=mock_tool_calls, conversation_history=[]
)

print(f"  [OK] 构建了 {len(messages)} 条消息")
print("\n  消息结构:")
for i, msg in enumerate(messages):
    print(f"\n  [{i}] role: {msg['role']}")
    content_preview = (
        msg.get("content", "")[:80] + "..."
        if len(msg.get("content", "")) > 80
        else msg.get("content", "")
    )
    print(f"      content: {content_preview}")
    if "tool_calls" in msg:
        print(f"      tool_calls: {msg['tool_calls']}")
    if "tool_call_id" in msg:
        print(f"      tool_call_id: {msg['tool_call_id']}")

# 2. 验证 OpenAI API 格式要求
print("\n[2] 验证消息格式")


def validate_openai_messages(messages):
    """验证消息格式是否符合 OpenAI API 要求"""
    errors = []

    for i, msg in enumerate(messages):
        role = msg.get("role")

        # 检查 tool 消息前面必须有 assistant 消息带 tool_calls
        if role == "tool":
            if i == 0:
                errors.append(f"消息 {i}: tool 消息不能是第一个消息")
            else:
                prev_msg = messages[i - 1]
                if prev_msg.get("role") != "assistant":
                    errors.append(
                        f"消息 {i}: tool 消息前必须是 assistant 消息，实际是 {prev_msg.get('role')}"
                    )
                elif "tool_calls" not in prev_msg:
                    errors.append(f"消息 {i}: 前一个 assistant 消息必须包含 tool_calls")

    return errors


errors = validate_openai_messages(messages)
if errors:
    print("  [ERROR] 格式错误:")
    for error in errors:
        print(f"    - {error}")
else:
    print("  [OK] 消息格式符合 OpenAI API 要求")

# 3. 测试对话历史更新
print("\n[3] 测试对话历史更新")

# 模拟多轮对话
from decoupled_agent import DecoupledAgent, PerformanceMetrics, IntentType
from unittest.mock import MagicMock

# 创建模拟模型
mock_intent_model = MagicMock()
mock_main_model = MagicMock()

# 创建 agent
agent = DecoupledAgent(
    intent_model=mock_intent_model, main_model=mock_main_model, tools={}
)

# 模拟两轮对话
print("\n  模拟第1轮对话...")
agent.conversation_history = []
agent._update_history(
    user_input="北京天气怎么样？",
    response="北京今天天气晴朗，温度25°C。",
    tool_calls=mock_tool_calls,
)
print(f"  历史消息数: {len(agent.conversation_history)}")
for i, msg in enumerate(agent.conversation_history):
    print(f"    [{i}] {msg['role']}: {msg['content'][:40]}...")

print("\n  模拟第2轮对话...")
agent._update_history(
    user_input="那上海呢？", response="上海今天多云，温度23°C。", tool_calls=[]
)
print(f"  历史消息数: {len(agent.conversation_history)}")
for i, msg in enumerate(agent.conversation_history):
    print(f"    [{i}] {msg['role']}: {msg['content'][:40]}...")

# 验证历史格式
print("\n[4] 验证对话历史格式")
history_errors = validate_openai_messages(agent.conversation_history)
if history_errors:
    print("  [ERROR] 历史格式错误:")
    for error in history_errors:
        print(f"    - {error}")
else:
    print("  [OK] 对话历史格式正确")

# 5. 测试带历史的完整消息构建
print("\n[5] 测试带历史的完整消息构建")
full_messages = MessageBuilder.build_main_model_messages(
    user_input="广州天气怎么样？",
    tool_results=[],
    conversation_history=agent.conversation_history,
)

print(f"  完整消息数: {len(full_messages)}")
full_errors = validate_openai_messages(full_messages)
if full_errors:
    print("  [ERROR] 完整消息格式错误:")
    for error in full_errors:
        print(f"    - {error}")
else:
    print("  [OK] 完整消息格式正确")

print("\n" + "=" * 80)
print("验证完成")
print("=" * 80)
print("\n关键修复：")
print("  - 不在 conversation_history 中添加 tool 消息")
print("  - 工具结果只在当前轮次通过上下文传递给主模型")
print("  - 避免 OpenAI API 的 'tool message without tool_calls' 错误")
