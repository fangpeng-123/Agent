# -*- coding: utf-8 -*-
"""工具执行器"""

import asyncio
import time
from typing import Any, Callable, Dict, List

from src.utils import ToolCall


class ToolExecutor:
    """工具执行器"""

    def __init__(self, functions: Dict[str, Callable]):
        self.functions = functions

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCall:
        start_time = time.time()

        if tool_name not in self.functions:
            result = f"[ERROR] 未找到工具: {tool_name}"
        else:
            try:
                func = self.functions[tool_name]
                if asyncio.iscoroutinefunction(func):
                    result = await func(**arguments)
                else:
                    result = func(**arguments)
            except Exception as e:
                result = f"[ERROR] 工具执行失败: {str(e)}"

        end_time = time.time()

        return ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            start_time=start_time,
            end_time=end_time,
        )

    async def execute_multiple(self, tool_calls: List[Dict]) -> List[ToolCall]:
        results = []
        for tc in tool_calls:
            result = await self.execute(tc["name"], tc.get("arguments", {}))
            results.append(result)
        return results
