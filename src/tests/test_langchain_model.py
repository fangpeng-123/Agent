# -*- coding: utf-8 -*-
"""基础 LangChain 模型调用测试"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import time
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv()


def test_model_basic():
    """基础模型调用测试"""
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        print("[ERROR] 未设置 API_KEY 环境变量")
        return

    print("=" * 60)
    print("[INFO] 开始模型调用测试")
    print("=" * 60)

    total_start = time.time()

    model = ChatOpenAI(
        model="qwen3-235b-a22b",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(API_KEY) if API_KEY else None,
        temperature=0.7,
        streaming=False,
    )

    ttft_start = time.time()
    response = model.invoke("你好，请简单介绍一下你自己")
    ttft = (time.time() - ttft_start) * 1000

    total_time = (time.time() - total_start) * 1000

    content = response.content if hasattr(response, "content") else str(response)

    print(f"\n[OK] 模型响应:")
    print("-" * 60)
    print(content)
    print("-" * 60)

    print(f"\n[性能统计]")
    print(f"  TTFT(首token延迟): {ttft:.2f} ms")
    print(f"  总耗时: {total_time:.2f} ms")
    print("=" * 60)


async def test_model_async():
    """异步模型调用测试"""
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr
    import asyncio
    import os
    from dotenv import load_dotenv

    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    if not API_KEY:
        print("[ERROR] 未设置 API_KEY 环境变量")
        return

    print("\n" + "=" * 60)
    print("[INFO] 开始异步模型调用测试")
    print("=" * 60)

    total_start = time.time()

    model = ChatOpenAI(
        model="qwen3-235b-a22b",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(API_KEY) if API_KEY else None,
        temperature=0.7,
        streaming=False,
    )

    ttft_start = time.time()
    response = await model.ainvoke("合肥今天天气怎么样？")
    ttft = (time.time() - ttft_start) * 1000

    total_time = (time.time() - total_start) * 1000

    content = response.content if hasattr(response, "content") else str(response)

    print(f"\n[OK] 模型响应:")
    print("-" * 60)
    print(content)
    print("-" * 60)

    print(f"\n[性能统计]")
    print(f"  TTFT(首token延迟): {ttft:.2f} ms")
    print(f"  总耗时: {total_time:.2f} ms")
    print("=" * 60)


async def test_model_streaming():
    """流式模型调用测试"""
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr
    import asyncio
    import os
    from dotenv import load_dotenv

    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    if not API_KEY:
        print("[ERROR] 未设置 API_KEY 环境变量")
        return

    print("\n" + "=" * 60)
    print("[INFO] 开始流式模型调用测试")
    print("=" * 60)

    total_start = time.time()

    model = ChatOpenAI(
        model="qwen3-235b-a22b",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(API_KEY) if API_KEY else None,
        temperature=0.7,
        streaming=True,
    )

    messages = [{"role": "user", "content": "请用50字以内描述春天的特点"}]

    first_token_time = None
    content = ""
    token_count = 0

    ttft_start = time.time()

    async for chunk in model.astream(messages):
        text = chunk.content if hasattr(chunk, "content") else str(chunk)
        if not first_token_time:
            first_token_time = (time.time() - ttft_start) * 1000
        content += text if isinstance(text, str) else ""
        token_count += 1

    total_time = (time.time() - total_start) * 1000

    print(f"\n[OK] 模型响应:")
    print("-" * 60)
    print(content)
    print("-" * 60)

    print(f"\n[性能统计]")
    print(f"  TTFT(首token延迟): {first_token_time:.2f} ms")
    print(f"  总耗时: {total_time:.2f} ms")
    print(f"  生成token数: {token_count}")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio

    test_model_basic()

    asyncio.run(test_model_async())

    asyncio.run(test_model_streaming())
