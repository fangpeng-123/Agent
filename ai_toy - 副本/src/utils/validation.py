# -*- coding: utf-8 -*-
"""工具函数"""

from pydantic import BaseModel


def validate_model(model: BaseModel, data: dict) -> tuple[bool, dict]:
    """验证 Pydantic 模型"""
    try:
        instance = model(**data)
        return True, instance.model_dump()
    except Exception as e:
        return False, {"error": str(e)}
