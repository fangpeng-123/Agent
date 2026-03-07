# -*- coding: utf-8 -*-
"""天气工具智能体"""

import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()


def get_agent_model():
    """获取工具智能体模型"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    return ChatOpenAI(
        model="qwen3-30b-a3b",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(api_key) if api_key else None,
        temperature=0.1,
        extra_body={"enable_thinking": False},
    )


class WeatherAgent:
    """天气工具智能体基类"""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.model = get_agent_model()
        from .agent_prompts import WEATHER_AGENT_PROMPTS

        self.system_prompt = WEATHER_AGENT_PROMPTS.get(tool_name, "")
        self.functions = {
            "get_weather_now": self._get_weather_now,
            "get_weather_forecast": self._get_weather_forecast,
            "get_hourly_forecast": self._get_hourly_forecast,
            "get_air_quality": self._get_air_quality,
            "get_life_index": self._get_life_index,
            "search_city": self._search_city,
        }

    async def run(self, user_input: str, requery_params: Dict) -> Dict[str, Any]:
        """执行智能体判断"""
        prompt_content = self.system_prompt.replace("{input}", user_input).replace(
            "{params}", json.dumps(requery_params, ensure_ascii=False)
        )

        messages = [
            SystemMessage(content=prompt_content),
            HumanMessage(content=user_input),
        ]

        response = await self.model.ainvoke(messages)

        try:
            content = response.content
            if isinstance(content, list):
                content = str(content)
            result = json.loads(content)
        except (json.JSONDecodeError, TypeError, ValueError):
            result = {"use_tool": False, "reason": "JSON解析失败", "result": None}

        if result.get("use_tool", False) and self.tool_name in self.functions:
            func = self.functions[self.tool_name]
            try:
                tool_params = self._extract_tool_params(requery_params)
                result["result"] = await func(**tool_params)
            except Exception as e:
                result["result"] = f"工具执行失败: {str(e)}"

        return result

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        """从 ReQuery 参数中提取工具所需参数"""
        return requery_params

    async def _get_weather_now(self, location: str) -> str:
        from .Weather import get_weather_now

        return await get_weather_now(location)

    async def _get_weather_forecast(self, location: str, days: int = 3) -> str:
        from .Weather import get_weather_forecast

        return await get_weather_forecast(location, days)

    async def _get_hourly_forecast(self, location: str, hours: int = 24) -> str:
        from .Weather import get_hourly_forecast

        return await get_hourly_forecast(location, hours)

    async def _get_air_quality(self, location: str) -> str:
        from .Weather import get_air_quality

        return await get_air_quality(location)

    async def _get_life_index(self, location: str) -> str:
        from .Weather import get_life_index

        return await get_life_index(location)

    async def _search_city(self, city_name: str, country: str = "CN") -> str:
        from .Weather import search_city

        return await search_city(city_name, country)


class GetWeatherNowAgent(WeatherAgent):
    """实时天气智能体"""

    def __init__(self):
        super().__init__("get_weather_now")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        return {"location": requery_params.get("location", "")}


class GetWeatherForecastAgent(WeatherAgent):
    """天气预报智能体"""

    def __init__(self):
        super().__init__("get_weather_forecast")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        days = requery_params.get("days", 3)
        valid_days = [3, 7, 10, 15, 30]
        if days not in valid_days:
            for v in valid_days:
                if v >= days:
                    days = v
                    break
            else:
                days = 3
        return {
            "location": requery_params.get("location", ""),
            "days": days,
        }


class GetHourlyForecastAgent(WeatherAgent):
    """逐小时预报智能体"""

    def __init__(self):
        super().__init__("get_hourly_forecast")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        return {
            "location": requery_params.get("location", ""),
            "hours": requery_params.get("hours", 24),
        }


class GetAirQualityAgent(WeatherAgent):
    """空气质量智能体"""

    def __init__(self):
        super().__init__("get_air_quality")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        return {"location": requery_params.get("location", "")}


class GetLifeIndexAgent(WeatherAgent):
    """生活指数智能体"""

    def __init__(self):
        super().__init__("get_life_index")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        return {"location": requery_params.get("location", "")}


class SearchCityAgent(WeatherAgent):
    """城市搜索智能体"""

    def __init__(self):
        super().__init__("search_city")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        return {
            "city_name": requery_params.get("city_name", ""),
            "country": requery_params.get("country", "CN"),
        }


WEATHER_AGENTS = {
    "get_weather_now": GetWeatherNowAgent(),
    "get_weather_forecast": GetWeatherForecastAgent(),
    "get_hourly_forecast": GetHourlyForecastAgent(),
    "get_air_quality": GetAirQualityAgent(),
    "get_life_index": GetLifeIndexAgent(),
    "search_city": SearchCityAgent(),
}
