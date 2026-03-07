# -*- coding: utf-8 -*-
"""完整流水线集成测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def test_full_pipeline():
    """测试完整流水线"""
    from src.agent_core import DecoupledAgent
    from langchain_openai import ChatOpenAI

    # 此测试需要真实 API Key
    print("完整流水线测试需要 API Key")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_full_pipeline())
