# -*- coding: utf-8 -*-
"""工具执行单元测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def test_tool_execution():
    """测试工具执行"""
    from src.tool_executor import ToolExecutor

    def dummy_tool(name: str):
        return f"Hello, {name}!"

    executor = ToolExecutor({"greet": dummy_tool})
    result = await executor.execute("greet", {"name": "World"})
    assert "World" in result.result


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_tool_execution())
    print("工具执行测试通过！")
