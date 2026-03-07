# -*- coding: utf-8 -*-
"""安全检查器"""

from src.security.content_filter import ContentFilter


class SafetyChecker:
    """综合安全检查器"""

    def __init__(self):
        self.content_filter = ContentFilter()

    async def check_input(
        self, text: str, is_child_mode: bool = False
    ) -> tuple[bool, str]:
        """
        检查用户输入安全性

        Args:
            text: 用户输入
            is_child_mode: 是否为儿童模式

        Returns:
            (is_safe, error_message)
        """
        if is_child_mode:
            return self.content_filter.check_child_safe(text)
        return self.content_filter.filter(text)

    async def check_output(
        self, text: str, is_child_mode: bool = False
    ) -> tuple[bool, str]:
        """
        检查输出内容安全性

        Args:
            text: 模型输出
            is_child_mode: 是否为儿童模式

        Returns:
            (is_safe, error_message)
        """
        if is_child_mode:
            return self.content_filter.check_child_safe(text)
        return self.content_filter.filter(text)
