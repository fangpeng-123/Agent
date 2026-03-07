# -*- coding: utf-8 -*-
"""知识库工具"""

from typing import Dict, List


def search_knowledge_base(query: str, top_k: int = 5) -> List[Dict]:
    """
    搜索知识库

    Args:
        query: 查询内容
        top_k: 返回结果数量

    Returns:
        相关知识条目列表
    """
    return [{"title": "知识条目", "content": f"关于 {query} 的知识", "score": 0.9}]


def get_knowledge_entry(entry_id: str) -> Dict:
    """
    获取知识条目

    Args:
        entry_id: 条目 ID

    Returns:
        知识条目内容
    """
    return {"id": entry_id, "title": "知识条目", "content": "内容..."}


def add_knowledge_entry(title: str, content: str, category: str = "general") -> str:
    """
    添加知识条目

    Args:
        title: 标题
        content: 内容
        category: 分类

    Returns:
        新增条目 ID
    """
    return f"entry_{hash(title) % 10000}"
