# -*- coding: utf-8 -*-
"""
日期时间 Function Call 工具
提供日期时间查询功能的函数调用实现
"""

from datetime import datetime
from typing import Dict, Any, List

DATETIME_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_datetime_info",
            "description": "获取日期时间信息，包括年月日、星期几、当前时间等。当用户询问今天是几号、星期几、现在几点等时间相关问题时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["date", "weekday", "time", "full"],
                        "description": "查询类型：date=日期(年月日), weekday=星期几, time=当前时间, full=完整信息",
                    }
                },
                "required": [],
            },
        },
    }
]

WEEKDAY_NAMES = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


async def get_datetime_info(query_type: str = "full") -> str:
    """
    获取日期时间信息

    Args:
        query_type: 查询类型
            - date: 返回年月日
            - weekday: 返回星期几
            - time: 返回当前时间
            - full: 返回完整信息

    Returns:
        日期时间信息
    """
    now = datetime.now()

    if query_type == "date":
        return f"今天是{now.year}年{now.month}月{now.day}日"

    elif query_type == "weekday":
        weekday_name = WEEKDAY_NAMES[now.weekday()]
        return f"今天是{weekday_name}"

    elif query_type == "time":
        hour = now.hour
        minute = now.minute

        if hour < 6:
            period = "凌晨"
        elif hour < 9:
            period = "早上"
        elif hour < 12:
            period = "上午"
        elif hour < 14:
            period = "中午"
        elif hour < 17:
            period = "下午"
        elif hour < 19:
            period = "傍晚"
        else:
            period = "晚上"

        return f"现在是{period}{hour}点{minute}分"

    else:
        weekday_name = WEEKDAY_NAMES[now.weekday()]

        hour = now.hour
        minute = now.minute

        if hour < 6:
            period = "凌晨"
        elif hour < 9:
            period = "早上"
        elif hour < 12:
            period = "上午"
        elif hour < 14:
            period = "中午"
        elif hour < 17:
            period = "下午"
        elif hour < 19:
            period = "傍晚"
        else:
            period = "晚上"

        return f"今天是{now.year}年{now.month}月{now.day}日，{weekday_name}，{period}{hour}点{minute}分"


DATETIME_FUNCTIONS = {
    "get_datetime_info": get_datetime_info,
}


if __name__ == "__main__":
    import asyncio

    print("[INFO] 日期时间 Function Call 工具测试")
    print("-" * 50)
    print(f"[OK] 已加载 {len(DATETIME_TOOLS)} 个日期时间工具")

    print("\n测试各种查询类型:")
    for query_type in ["date", "weekday", "time", "full"]:
        result = asyncio.run(get_datetime_info(query_type))
        print(f"  [{query_type}] {result}")
