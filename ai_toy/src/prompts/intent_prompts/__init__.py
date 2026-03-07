# -*- coding: utf-8 -*-
"""Intent Prompt 模板"""

from src.prompts.intent_prompts.classifier import INTENT_CLASSIFIER_PROMPT
from src.prompts.intent_prompts.query_rewriter import QUERY_REWRITER_PROMPT

INTENT_PROMPTS = {
    "classifier": INTENT_CLASSIFIER_PROMPT,
    "rewriter": QUERY_REWRITER_PROMPT,
}

__all__ = ["INTENT_PROMPTS", "INTENT_CLASSIFIER_PROMPT", "QUERY_REWRITER_PROMPT"]
