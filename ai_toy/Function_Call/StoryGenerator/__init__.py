# -*- coding: utf-8 -*-
"""故事生成工具"""

from typing import Dict


def generate_story(
    theme: str, length: str = "short", age_group: str = "children"
) -> str:
    """
    生成故事

    Args:
        theme: 故事主题
        length: 故事长度 (short/medium/long)
        age_group: 年龄组 (children/teenagers/adults)

    Returns:
        生成的故事内容
    """
    return f"[故事生成] 主题: {theme}, 长度: {length}"


def generate_fairy_tale(protagonist: str, moral: str) -> str:
    """
    生成童话故事

    Args:
        protagonist: 主人公
        moral: 故事寓意

    Returns:
        童话故事内容
    """
    return f"[童话] 主人公: {protagonist}, 寓意: {moral}"


def generate_educational_story(topic: str) -> str:
    """
    生成教育故事

    Args:
        topic: 教育主题

    Returns:
        教育故事内容
    """
    return f"[教育故事] 主题: {topic}"
