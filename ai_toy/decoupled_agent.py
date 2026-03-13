# -*- coding: utf-8 -*-
"""
解耦智能体架构设计
包含意图路由、工具调用、性能监控的完整实现
"""

import asyncio
import time

from src.core import DecoupledAgent, PROGRAM_START, TOOLS_LOAD_DURATION_MS
from src.utils import IntentType


async def example_usage():
    """使用示例"""
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr
    import os
    from dotenv import load_dotenv

    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    main_model = ChatOpenAI(
        model="qwen3-235b-a22b-instruct-2507",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(API_KEY) if API_KEY else None,
        temperature=0.7,
        streaming=True,
        extra_body={"enable_thinking": False},
    )

    from src.services.tts_service import TTSConfig

    tts_config = TTSConfig(speed=1.0)
    agent = DecoupledAgent(main_model=main_model, tts_config=tts_config)

    # 初始化时预加载用户画像
    await agent.init_user_profile()

    print("=" * 80)
    print("连续对话模式已启动，输入 'quit' 或 'exit' 退出")
    print("=" * 80)

    while True:
        try:
            user_input = input("\n用户: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出程序")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "退出"]:
            # 退出前等待画像更新完成
            await agent.flush_user_profile()
            print("再见！")
            break

        print("=" * 80)

        response = await agent.process(user_input, stream=True)

        print(f"\n意图: {response.intent.value}")

        if response.tool_calls:
            print(f"\n工具调用:")
            for tc in response.tool_calls:
                print(f"  - {tc.tool_name}: {tc.duration_ms:.2f} ms")

        if response.metrics:
            response.metrics.print_report(include_tools_loaded=True)


if __name__ == "__main__":
    asyncio.run(example_usage())
