# -*- coding: utf-8 -*-
"""敏感词过滤"""

from pathlib import Path
from typing import List, Set


class ContentFilter:
    """内容过滤器"""

    def __init__(self, keyword_dir: str = "./src/security/keywords"):
        self.keyword_dir = Path(keyword_dir)
        self.keyword_sets: dict[str, Set[str]] = {}
        self._load_keywords()

    def _load_keywords(self):
        """加载敏感词库"""
        if not self.keyword_dir.exists():
            return

        for file_path in self.keyword_dir.glob("*.txt"):
            category = file_path.stem
            keywords = set()
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word:
                        keywords.add(word)
            self.keyword_sets[category] = keywords

    def filter(self, text: str) -> tuple[bool, List[str]]:
        """
        检查文本是否包含敏感词

        Returns:
            (is_safe, matched_keywords)
        """
        matched = []
        for category, keywords in self.keyword_sets.items():
            for keyword in keywords:
                if keyword in text:
                    matched.append(f"[{category}] {keyword}")
        return len(matched) == 0, matched

    def check_child_safe(self, text: str) -> tuple[bool, str]:
        """儿童场景安全检查"""
        is_safe, matched = self.filter(text)
        if not is_safe:
            return False, f"内容包含不当词汇: {', '.join(matched)}"
        return True, ""
