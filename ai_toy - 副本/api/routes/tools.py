# -*- coding: utf-8 -*-
"""工具接口"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/list")
async def list_tools():
    """列出所有可用工具"""
    return {"tools": "TODO: 实现工具列表接口"}


@router.post("/execute")
async def execute_tool(tool_name: str, params: dict):
    """执行工具"""
    return {
        "tool_name": tool_name,
        "params": params,
        "result": "TODO: 实现工具执行接口",
    }
