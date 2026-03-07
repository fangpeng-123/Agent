# -*- coding: utf-8 -*-
"""地图工具智能体"""

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


class MapAgent:
    """地图工具智能体基类"""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.model = get_agent_model()
        from .agent_prompts import MAP_AGENT_PROMPTS

        self.system_prompt = MAP_AGENT_PROMPTS.get(tool_name, "")
        self.functions = {
            "geocode": self._geocode,
            "reverse_geocode": self._reverse_geocode,
            "place_search": self._place_search,
            "get_direction": self._get_direction,
            "get_ip_location": self._get_ip_location,
        }

    async def run(self, user_input: str, requery_params: Dict) -> Dict[str, Any]:
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
        return requery_params

    async def _geocode(self, address: str) -> str:
        from .Map import geocode

        return await geocode(address)

    async def _reverse_geocode(self, lat: float, lng: float) -> str:
        from .Map import reverse_geocode

        return await reverse_geocode(lat, lng)

    async def _place_search(
        self, query: str, region: str = "全国", page_size: int = 10
    ) -> str:
        from .Map import place_search

        return await place_search(query, region, page_size)

    async def _get_direction(
        self, origin: str, destination: str, mode: str = "driving"
    ) -> str:
        from .Map import get_direction

        return await get_direction(origin, destination, mode)

    async def _get_ip_location(self) -> str:
        from .Map import get_ip_location

        return await get_ip_location()


class GeocodeAgent(MapAgent):
    """地理编码智能体"""

    def __init__(self):
        super().__init__("geocode")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        return {"address": requery_params.get("address", "")}


class ReverseGeocodeAgent(MapAgent):
    """逆地理编码智能体"""

    def __init__(self):
        super().__init__("reverse_geocode")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        return {
            "lat": requery_params.get("lat", 0.0),
            "lng": requery_params.get("lng", 0.0),
        }


class PlaceSearchAgent(MapAgent):
    """地点搜索智能体"""

    def __init__(self):
        super().__init__("place_search")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        return {
            "query": requery_params.get("query", ""),
            "region": requery_params.get("region", "全国"),
            "page_size": requery_params.get("page_size", 10),
        }


class GetDirectionAgent(MapAgent):
    """路线规划智能体"""

    def __init__(self):
        super().__init__("get_direction")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        return {
            "origin": requery_params.get("origin", ""),
            "destination": requery_params.get("destination", ""),
            "mode": requery_params.get("mode", "driving"),
        }


class GetIPLocationAgent(MapAgent):
    """IP定位智能体"""

    def __init__(self):
        super().__init__("get_ip_location")

    def _extract_tool_params(self, requery_params: Dict) -> Dict:
        return {}


MAP_AGENTS = {
    "geocode": GeocodeAgent(),
    "reverse_geocode": ReverseGeocodeAgent(),
    "place_search": PlaceSearchAgent(),
    "get_direction": GetDirectionAgent(),
    "get_ip_location": GetIPLocationAgent(),
}
