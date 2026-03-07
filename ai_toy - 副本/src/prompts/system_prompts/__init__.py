# -*- coding: utf-8 -*-
"""System Prompt 模板"""

from src.prompts.system_prompts.base import SYSTEM_PROMPTS
from src.prompts.system_prompts.child_companion import CHILD_COMPANION_PROMPT
from src.prompts.system_prompts.few_shots import FEW_SHOT_EXAMPLES

__all__ = ["SYSTEM_PROMPTS", "CHILD_COMPANION_PROMPT", "FEW_SHOT_EXAMPLES"]
