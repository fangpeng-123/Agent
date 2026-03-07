"""
内容安全服务
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SafetyResult:
    passed: bool
    reason: str = ""
    filtered_text: str = ""


class SafetyService:
    """内容安全服务"""

    DEFAULT_SENSITIVE_WORDS = [
        "分裂",
        "叛乱",
        "颠覆",
        "暴动",
        "恐怖",
        "色情",
        "毒品",
        "赌博",
        "诈骗",
    ]

    def __init__(self, sensitive_words: List[str] = None):
        self.sensitive_words = sensitive_words or self.DEFAULT_SENSITIVE_WORDS
        self._pattern = self._compile_pattern()

    def _compile_pattern(self):
        """编译正则"""
        pattern = "|".join(re.escape(w) for w in self.sensitive_words)
        return re.compile(pattern) if pattern else None

    def check_input(self, text: str) -> SafetyResult:
        """检查输入"""
        if not text or not text.strip():
            return SafetyResult(passed=True)

        if self._pattern:
            match = self._pattern.search(text)
            if match:
                return SafetyResult(passed=False, reason=f"包含敏感词: {match.group()}")

        return SafetyResult(passed=True)

    def contains_legal_keywords(self, text: str) -> bool:
        """检查是否包含法律关键词"""
        legal_keywords = [
            "法",
            "条",
            "款",
            "罪",
            "刑",
            "民",
            "诉",
            "权",
            "义务",
            "责任",
            "合同",
            "赔偿",
            "宪法",
        ]
        return any(kw in text for kw in legal_keywords)

    def is_valid_question(self, text: str) -> Tuple[bool, str]:
        """检查是否为有效问题"""
        text = text.strip()

        if len(text) < 2:
            return False, "问题太短"

        if not self.contains_legal_keywords(text):
            return False, "未检测到法律相关关键词"

        check_result = self.check_input(text)
        if not check_result.passed:
            return False, check_result.reason

        return True, ""
