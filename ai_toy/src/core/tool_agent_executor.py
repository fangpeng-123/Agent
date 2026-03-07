# -*- coding: utf-8 -*-
"""工具智能体并行执行器"""

import asyncio
from typing import Dict, List, Any
from Function_Call import ALL_AGENTS


class ToolAgentExecutor:
    """工具智能体并行执行器"""

    def __init__(self):
        self.agents = ALL_AGENTS

    async def execute_all(
        self, rewritten_query: str, requery_params: Dict
    ) -> List[Dict]:
        """并行执行所有工具智能体"""
        tasks = []
        for tool_name, agent in self.agents.items():
            task = self._execute_single(
                tool_name, agent, rewritten_query, requery_params
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        tool_results = []
        for tool_name, result in zip(self.agents.keys(), results):
            if isinstance(result, Exception):
                tool_results.append(
                    {
                        "tool": tool_name,
                        "use_tool": False,
                        "reason": f"执行异常: {str(result)}",
                        "result": None,
                    }
                )
            else:
                tool_results.append({"tool": tool_name, **result})

        return tool_results

    async def _execute_single(
        self, tool_name: str, agent, rewritten_query: str, requery_params: Dict
    ) -> Dict[str, Any]:
        """执行单个工具智能体"""
        return await agent.run(rewritten_query, requery_params)
