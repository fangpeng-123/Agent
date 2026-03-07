# -*- coding: utf-8 -*-
"""健康检查接口"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthStatus(BaseModel):
    """健康状态"""

    status: str
    version: str = "1.0.0"


@router.get("/", response_model=HealthStatus)
async def health_check():
    """健康检查"""
    return HealthStatus(status="healthy")


@router.get("/ready")
async def readiness_check():
    """就绪检查"""
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """存活检查"""
    return {"alive": True}
