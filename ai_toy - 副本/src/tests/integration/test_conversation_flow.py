# -*- coding: utf-8 -*-
"""对话流程集成测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def test_conversation_flow():
    """测试对话流程"""
    from src.memory import ConversationManager

    manager = ConversationManager()
    context = await manager.process_message(
        conversation_id="test_001",
        user_id="user_001",
        message="你好",
    )
    assert "message" in context
    assert "history" in context


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_conversation_flow())
    print("对话流程测试通过！")
