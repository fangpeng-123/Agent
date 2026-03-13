# -*- coding: utf-8 -*-
"""
上下文管理器

功能：
1. 管理用户上下文信息（地点、天气、日期时间）
2. 从用户画像获取地点信息
3. 定时更新天气信息
4. 提供上下文信息格式化
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from Function_Call.UserProfile.user_profile_tools import USER_PROFILES


# 用户画像文件路径
USER_PROFILES_FILE = (
    Path(__file__).parent.parent
    / "Function_Call"
    / "UserProfile"
    / "user_profiles.json"
)


def load_user_profiles_from_file() -> Dict[str, Dict]:
    """从文件加载用户画像"""
    try:
        if USER_PROFILES_FILE.exists():
            with open(USER_PROFILES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] 加载用户画像文件失败: {e}")
    return {}


class ContextCache:
    """上下文缓存"""

    # 天气缓存过期时间（秒）：1小时
    WEATHER_CACHE_TTL = 3600

    def __init__(self):
        # 按 user_id 隔离缓存
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """获取用户上下文"""
        if user_id not in self._cache:
            self._cache[user_id] = {
                "location": "",  # 地点
                "weather": "",  # 天气信息
                "weather_updated": 0,  # 天气更新时间
                "datetime": "",  # 日期时间
            }
        return self._cache[user_id]

    def set_location(self, user_id: str, location: str):
        """设置地点"""
        ctx = self.get_user_context(user_id)
        ctx["location"] = location

    def get_location(self, user_id: str) -> str:
        """获取地点"""
        ctx = self.get_user_context(user_id)
        return ctx.get("location", "")

    def set_weather(self, user_id: str, weather: str):
        """设置天气信息"""
        ctx = self.get_user_context(user_id)
        ctx["weather"] = weather
        ctx["weather_updated"] = time.time()

    def get_weather(self, user_id: str) -> str:
        """获取天气信息（检查是否过期）"""
        ctx = self.get_user_context(user_id)

        # 检查是否过期
        if time.time() - ctx.get("weather_updated", 0) > self.WEATHER_CACHE_TTL:
            return ""  # 过期返回空

        return ctx.get("weather", "")

    def is_weather_expired(self, user_id: str) -> bool:
        """检查天气是否过期"""
        ctx = self.get_user_context(user_id)
        return time.time() - ctx.get("weather_updated", 0) > self.WEATHER_CACHE_TTL

    def set_datetime(self, user_id: str, datetime_info: str):
        """设置日期时间"""
        ctx = self.get_user_context(user_id)
        ctx["datetime"] = datetime_info

    def get_datetime(self, user_id: str) -> str:
        """获取日期时间"""
        ctx = self.get_user_context(user_id)
        return ctx.get("datetime", "")

    def clear(self, user_id: str):
        """清除用户上下文"""
        if user_id in self._cache:
            del self._cache[user_id]


# 全局缓存实例
_context_cache: Optional[ContextCache] = None


def get_context_cache() -> ContextCache:
    """获取全局上下文缓存"""
    global _context_cache
    if _context_cache is None:
        _context_cache = ContextCache()
    return _context_cache


class ContextManager:
    """上下文管理器"""

    def __init__(self, user_id: str = "user_001"):
        self.user_id = user_id
        self.cache = get_context_cache()

    async def init_context(self):
        """初始化上下文（从用户画像加载地点、天气、日期时间）"""
        # 1. 加载用户画像
        loaded = load_user_profiles_from_file()
        USER_PROFILES.update(loaded)

        profile = USER_PROFILES.get(self.user_id, {})

        # 2. 获取地点
        location = profile.get("location", "")
        if location:
            self.cache.set_location(self.user_id, location)

        # 3. 获取日期时间（启动时获取最新）
        await self.update_datetime()

        # 4. 尝试获取天气（如果已过期）
        await self._update_weather_if_needed()

    async def _update_weather_if_needed(self):
        """如果天气过期则更新"""
        if self.cache.is_weather_expired(self.user_id):
            await self.update_weather()

    async def update_weather(self):
        """更新天气信息"""
        location = self.cache.get_location(self.user_id)
        if not location:
            return

        try:
            # 调用天气工具获取天气
            from Function_Call.Weather import get_weather_now

            weather = await get_weather_now(location)
            self.cache.set_weather(self.user_id, weather)
        except Exception as e:
            print(f"[WARN] 获取天气失败: {e}")
            self.cache.set_weather(self.user_id, "")

    async def update_datetime(self):
        """更新日期时间信息"""
        try:
            from Function_Call.DateTime import get_datetime_info

            datetime_info = await get_datetime_info("full")
            self.cache.set_datetime(self.user_id, datetime_info)
        except Exception as e:
            print(f"[WARN] 获取日期时间失败: {e}")
            self.cache.set_datetime(self.user_id, "")

    def get_context_info(self) -> str:
        """获取格式化后的上下文信息"""
        location = self.cache.get_location(self.user_id)
        weather = self.cache.get_weather(self.user_id)
        datetime_info = self.cache.get_datetime(self.user_id)

        # 构建上下文字符串
        parts = []

        if location:
            parts.append(f"用户所在地: {location}")

        if weather:
            parts.append(f"当前天气: {weather}")

        if datetime_info:
            parts.append(f"当前时间: {datetime_info}")

        if not parts:
            return ""

        return "【上下文信息】\n" + "\n".join(parts)

    def get_location(self) -> str:
        """获取地点"""
        return self.cache.get_location(self.user_id)

    def is_weather_expired(self) -> bool:
        """检查天气是否过期"""
        return self.cache.is_weather_expired(self.user_id)


# 全局上下文管理器实例
_context_managers: Dict[str, ContextManager] = {}


def get_context_manager(user_id: str = "user_001") -> ContextManager:
    """获取上下文管理器实例"""
    if user_id not in _context_managers:
        _context_managers[user_id] = ContextManager(user_id)
    return _context_managers[user_id]


async def init_user_context(user_id: str = "user_001"):
    """初始化用户上下文"""
    manager = get_context_manager(user_id)
    await manager.init_context()


if __name__ == "__main__":
    import asyncio

    async def test():
        # 测试上下文管理器
        manager = ContextManager("user_001")

        # 初始化
        await manager.init_context()

        # 获取上下文信息
        print("=== 上下文信息 ===")
        print(manager.get_context_info())

        print("\n=== 地点 ===")
        print(manager.get_location())

        print("\n=== 天气过期？ ===")
        print(manager.is_weather_expired())

    asyncio.run(test())
