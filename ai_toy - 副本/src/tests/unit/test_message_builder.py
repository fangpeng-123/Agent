# -*- coding: utf-8 -*-
"""消息构建器单元测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.message_builder import MessageBuilder
from src.performance import ToolCall


def test_build_messages_without_tools():
    """测试无工具的消息构建"""
    messages = MessageBuilder.build_main_model_messages(
        user_input="你好",
        tool_results=[],
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"


def test_build_messages_with_history():
    """测试带历史的消息构建"""
    messages = MessageBuilder.build_main_model_messages(
        user_input="今天天气怎么样？",
        tool_results=[],
        conversation_history=[{"role": "user", "content": "你好"}],
    )
    assert len(messages) == 3


if __name__ == "__main__":
    test_build_messages_without_tools()
    test_build_messages_with_history()
    print("消息构建器测试通过！")
