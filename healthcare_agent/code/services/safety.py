from typing import List
import ahocorasick


class SafetyService:
    def __init__(self, sensitive_words: List[str]):
        self.sensitive_words = sensitive_words
        self.automaton = self._build_automaton()

    def _build_automaton(self):
        automaton = ahocorasick.Automaton()
        for word in self.sensitive_words:
            automaton.add_word(word, word)
        automaton.make_automaton()
        return automaton

    def is_valid_question(self, question: str) -> tuple[bool, str]:
        if not question or not question.strip():
            return False, "问题不能为空"

        for end_pos, word in self.automaton.iter(question):
            return False, f"问题包含敏感词: {word}"

        if len(question) > 500:
            return False, "问题长度不能超过500字"

        return True, ""

    def filter_content(self, content: str) -> str:
        filtered = content
        for end_pos, word in self.automaton.iter(content):
            filtered = filtered.replace(word, "*" * len(word))
        return filtered
