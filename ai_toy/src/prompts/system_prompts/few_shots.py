# -*- coding: utf-8 -*-
"""Few-Shot 示例库"""

FEW_SHOT_EXAMPLES = {
    "weather_query": [
        {
            "input": "北京今天天气怎么样？",
            "output": "北京今天晴天，气温3到15度，风不大，适合出门。",
        },
        {
            "input": "上海明天会下雨吗？",
            "output": "明天上海不会下雨，多云天气，气温12到20度。",
        },
        {
            "input": "广州后天天气呢？",
            "output": "后天广州有小雨，气温15到22度，出门记得带伞。",
        },
        {
            "input": "深圳这周天气怎么样？",
            "output": "深圳这几天都是多云，气温在18到26度左右，挺舒服的。",
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
