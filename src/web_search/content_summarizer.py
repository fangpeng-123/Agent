# -*- coding: utf-8 -*-
"""搜索结果摘要"""

from typing import List


class ContentSummarizer:
    """内容摘要器"""

    def __init__(self, max_length: int = 500):
        self.max_length = max_length

    async def summarize(self, content: str) -> str:
        """生成摘要"""
        if len(content) <= self.max_length:
            return content
        return content[: self.max_length] + "..."

    async def summarize_results(self, results: List[Dict]) -> str:
        """摘要搜索结果"""
        summaries = []
        for r in results:
            title = r.get("title", "")
            snippet = r.get("snippet", "")[:200]
            summaries.append(f"- {title}\n  {snippet}")
        return "\n".join(summaries)
