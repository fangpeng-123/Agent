# -*- coding: utf-8 -*-
"""天气接口"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/now")
async def get_weather_now(city: str):
    """获取当前天气"""
    return {"city": city, "weather": "TODO: 实现天气接口"}


@router.get("/forecast")
async def get_weather_forecast(city: str, days: int = 7):
    """获取天气预报"""
    return {"city": city, "days": days, "forecast": "TODO: 实现天气预报接口"}
