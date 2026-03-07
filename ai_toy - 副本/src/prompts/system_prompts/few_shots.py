# -*- coding: utf-8 -*-
"""Few-Shot 示例库"""

FEW_SHOT_EXAMPLES = {
    "weather_query": [
        {
            "input": "北京今天天气怎么样？",
            "output": "今天北京晴朗，最高气温15℃，最低气温3℃，适合外出。",
        },
        {
            "input": "上海明天会下雨吗？",
            "output": "上海明天多云转小雨，建议带伞。",
        },
    ],
    "greeting": [
        {
            "input": "你好！",
            "output": "你好！有什么我可以帮你的吗？",
        },
        {
            "input": "今天真开心！",
            "output": "听起来你今天心情很好！有什么开心的事想分享吗？",
        },
    ],
    "gratitude": [
        {
            "input": "谢谢你帮我查天气！",
            "output": "不客气！随时为你服务。",
        },
    ],
}


def get_few_shot_examples(example_type: str) -> list:
    """获取指定类型的 Few-Shot 示例"""
    return FEW_SHOT_EXAMPLES.get(example_type, [])
