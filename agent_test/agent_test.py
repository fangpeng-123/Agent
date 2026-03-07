# -*- coding: utf-8 -*-
"""
LangChain 1.x + MCP 智能体 - 流式输出版本
基础问题使用真流式，工具问题使用 Agent
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import SecretStr
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    stage_times: Dict[str, float] = field(default_factory=dict)
    chunk_times: List[Tuple[int, float, float]] = field(
        default_factory=list
    )  # (chunk_index, timestamp, delta_ms)
    tool_calls: List[Dict] = field(default_factory=list)

    def record(self, stage: str, timestamp: float | None = None):
        """记录某个阶段的时间戳"""
        if timestamp is None:
            timestamp = time.time()
        self.stage_times[stage] = timestamp
        return timestamp

    def record_chunk(self, chunk_index: int):
        """记录chunk到达时间"""
        current_time = time.time()
        if self.chunk_times:
            last_time = self.chunk_times[-1][1]
            delta = (current_time - last_time) * 1000
        else:
            delta = 0
        self.chunk_times.append((chunk_index, current_time, delta))
        return current_time

    def get_duration_ms(self, start_stage: str, end_stage: str = None) -> float:
        """计算两个stage之间的时间差（毫秒）"""
        if end_stage is None:
            end_stage = "end"
        if start_stage not in self.stage_times or end_stage not in self.stage_times:
            return 0.0
        return (self.stage_times[end_stage] - self.stage_times[start_stage]) * 1000

    def print_detailed_report(self):
        """打印详细性能报告"""
        print("\n" + "=" * 80)
        print("[详细性能分析报告]")
        print("=" * 80)

        # 按顺序打印各个阶段
        stage_order = [
            "request_start",
            "tool_detection",
            "agent_start",
            "first_chunk",
            "last_chunk",
            "response_end",
        ]

        print("\n[阶段耗时明细]")
        prev_stage = None
        for stage in stage_order:
            if stage in self.stage_times:
                if prev_stage:
                    duration = self.get_duration_ms(prev_stage, stage)
                    print(f"  {prev_stage} → {stage}: {duration:>8.2f} ms")
                prev_stage = stage

        if self.chunk_times:
            print(f"\n[Chunk传输分析] 共 {len(self.chunk_times)} 个chunk")
            print(
                f"  首chunk延迟: {(self.chunk_times[0][1] - self.stage_times.get('request_start', self.chunk_times[0][1])) * 1000:.2f} ms"
            )

            if len(self.chunk_times) > 1:
                avg_interval = sum(t[2] for t in self.chunk_times[1:]) / (
                    len(self.chunk_times) - 1
                )
                max_interval = max(self.chunk_times[1:], key=lambda x: x[2])
                min_interval = min(self.chunk_times[1:], key=lambda x: x[2])
                print(f"  平均chunk间隔: {avg_interval:.2f} ms")
                print(
                    f"  最大chunk间隔: {max_interval[2]:.2f} ms (chunk #{max_interval[0]})"
                )
                print(
                    f"  最小chunk间隔: {min_interval[2]:.2f} ms (chunk #{min_interval[0]})"
                )

            # 分析chunk分布
            if len(self.chunk_times) > 10:
                first_half = self.chunk_times[: len(self.chunk_times) // 2]
                second_half = self.chunk_times[len(self.chunk_times) // 2 :]
                first_duration = (first_half[-1][1] - first_half[0][1]) * 1000
                second_duration = (second_half[-1][1] - second_half[0][1]) * 1000
                print(
                    f"  前半段耗时: {first_duration:.2f} ms ({len(first_half)} chunks)"
                )
                print(
                    f"  后半段耗时: {second_duration:.2f} ms ({len(second_half)} chunks)"
                )

        print("\n[总耗时汇总]")
        if "request_start" in self.stage_times and "response_end" in self.stage_times:
            total = self.get_duration_ms("request_start", "response_end")
            print(f"  总响应时间: {total:.2f} ms ({total / 1000:.2f} s)")

        print("=" * 80)


model = ChatOpenAI(
    model="qwen3-235b-a22b",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr(API_KEY) if API_KEY else None,
    extra_body={"enable_thinking": False},
    streaming=True,
)

MCP_MAP_SERVER_PATH = r"F:\code\Agent\MCP\Map\server.py"
MCP_WEATHER_SERVER_PATH = r"F:\code\Agent\MCP\Weather\server.py"


def needs_tools(user_input: str) -> bool:
    """
    判断用户输入是否需要调用工具
    基于关键词判断，简单问候和基础问题不需要工具
    """
    user_input_lower = user_input.lower()

    # 需要工具的关键词
    tool_keywords = [
        # 天气相关
        "天气",
        "温度",
        "下雨",
        "晴",
        "阴",
        "风",
        "空气质量",
        "雾霾",
        # 地图相关
        "地图",
        "位置",
        "坐标",
        "经纬度",
        "路线",
        "导航",
        "怎么走",
        "附近",
        "周边",
        "距离",
        "多远",
        "在哪里",
        "地址",
        # 城市相关
        "北京",
        "上海",
        "广州",
        "深圳",
        "杭州",
        "南京",
        "合肥",
        # 动作
        "查",
        "查询",
        "搜索",
        "找",
        "定位",
    ]

    for keyword in tool_keywords:
        if keyword in user_input_lower:
            return True

    return False


async def stream_basic_response(messages, session_history, user_input):
    """
    基础问题的流式响应 - 直接使用 model.astream() 实现真正的逐字输出
    """
    full_response = ""

    async for chunk in model.astream(messages):
        if hasattr(chunk, "content") and chunk.content:
            text = str(chunk.content)
            full_response += text
            yield text

    if full_response:
        session_history.add_user_message(user_input)
        session_history.add_ai_message(full_response)


def extract_text_from_chunk(chunk):
    """从各种可能的 chunk 格式中提取文本"""
    text = ""

    if hasattr(chunk, "content") and chunk.content:
        text = str(chunk.content)
    elif isinstance(chunk, dict):
        if "model" in chunk and isinstance(chunk["model"], dict):
            model_data = chunk["model"]
            if "messages" in model_data and model_data["messages"]:
                for msg in model_data["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        text = str(msg.content)
                        break
        elif "output" in chunk:
            output = chunk["output"]
            if isinstance(output, str):
                text = output
            elif hasattr(output, "content"):
                text = str(output.content)
        elif "messages" in chunk and chunk["messages"]:
            for msg in chunk["messages"]:
                if hasattr(msg, "content") and msg.content:
                    text = str(msg.content)
                    break
        elif "content" in chunk and chunk["content"]:
            text = str(chunk["content"])
    elif isinstance(chunk, str):
        text = chunk

    return text


async def stream_agent_response(
    agent,
    messages,
    session_history,
    user_input,
    metrics: PerformanceMetrics | None = None,
):
    """
    流式生成 Agent 响应 - 带中间状态提示
    """
    full_response = ""
    chunk_index = 0
    has_shown_thinking = False
    has_shown_tool = False
    has_shown_generating = False
    tool_call_detected = False
    first_content_received = False

    if metrics:
        metrics.record("agent_start")

    # 立即显示思考状态
    yield "[正在分析您的需求...] "
    has_shown_thinking = True

    async for chunk in agent.astream({"messages": messages}):
        if metrics:
            if chunk_index == 0:
                metrics.record("first_chunk")
            metrics.record_chunk(chunk_index)

        # 检测chunk类型和内容
        chunk_type = None
        text = ""

        if isinstance(chunk, dict):
            # 检测中间步骤（工具调用）
            if "intermediate_steps" in chunk:
                chunk_type = "tool_call"
                tool_call_detected = True
                if not has_shown_tool:
                    yield "\n[正在查询相关信息...] "
                    has_shown_tool = True
                if metrics:
                    metrics.tool_calls.append(
                        {
                            "timestamp": time.time(),
                            "type": "intermediate_step",
                            "data": chunk["intermediate_steps"],
                        }
                    )
            # 检测最终输出
            elif "output" in chunk:
                chunk_type = "output"
                output = chunk["output"]
                if hasattr(output, "content"):
                    text = str(output.content)
                elif isinstance(output, str):
                    text = output
            elif "messages" in chunk and chunk["messages"]:
                chunk_type = "messages"
                last_message = chunk["messages"][-1]
                if hasattr(last_message, "content"):
                    text = str(last_message.content)
            elif "content" in chunk and chunk["content"]:
                chunk_type = "content"
                text = str(chunk["content"])
        elif hasattr(chunk, "content") and chunk.content:
            chunk_type = "content"
            text = str(chunk.content)

        # 处理文本内容
        if text and text != full_response:
            new_text = text[len(full_response) :]
            if new_text:
                # 第一次收到内容时，显示生成状态
                if not first_content_received and not has_shown_generating:
                    yield "\n[正在生成回答...]\n"
                    has_shown_generating = True
                    first_content_received = True
                full_response = text
                yield new_text

        chunk_index += 1

    if metrics:
        metrics.record("last_chunk")

    # 如果没有收到任何内容，使用非流式后备
    if not full_response:
        try:
            yield "\n[正在查询中，请稍候...]\n"
            response = await agent.ainvoke({"messages": messages})
            text = extract_text_from_response(response)
            if text:
                full_response = text
                yield text
        except Exception as e:
            print(f"[ERROR] 后备调用失败: {e}")

    if full_response:
        session_history.add_user_message(user_input)
        session_history.add_ai_message(full_response)


def extract_text_from_response(response):
    """从非流式响应中提取文本"""
    text = ""

    if hasattr(response, "messages") and response.messages:
        last_message = response.messages[-1]
        if hasattr(last_message, "content"):
            text = str(last_message.content)
    elif isinstance(response, dict) and "messages" in response:
        last_message = response["messages"][-1]
        if hasattr(last_message, "content"):
            text = str(last_message.content)
    elif hasattr(response, "content"):
        text = str(response.content)
    elif isinstance(response, str):
        text = response

    return text


async def main():
    """主函数"""
    print("=" * 80)
    print("LangChain 1.x + MCP 智能体 - 流式输出版本")
    print("=" * 80)

    print("\n[1] 初始化 MCP 连接...")

    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain.agents import create_agent
    from langchain_community.chat_message_histories import ChatMessageHistory

    server_config = {
        "map": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [MCP_MAP_SERVER_PATH],
        },
        "weather": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [MCP_WEATHER_SERVER_PATH],
        },
    }

    print("  连接 MCP 服务器...")
    client = MultiServerMCPClient(server_config)

    try:
        all_tools = await client.get_tools()
        print(f"  [OK] 加载了 {len(all_tools)} 个工具")
        for tool in all_tools:
            print(f"      - {tool.name}")

        print(f"\n[OK] 工具加载完成\n")

        print("[2] 创建 Agent...")
        agent = create_agent(
            model=model,
            tools=all_tools,
            system_prompt="You are a helpful assistant with access to map and weather tools. "
            "When users ask about locations, directions, or weather, use the appropriate tools to help them. "
            "Always respond in Chinese.",
        )
        print("[OK] Agent 创建成功\n")

        print("[3] 启动对话（智能流式模式）...")
        await run_conversation_streaming(agent)

    except Exception as e:
        print(f"\n[ERROR] 程序异常: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\n[INFO] 关闭 MCP 连接...")
        try:
            if hasattr(client, "aclose"):
                await client.aclose()
            elif hasattr(client, "close"):
                await client.close()
        except:
            pass

    print("[INFO] 程序正常退出")


async def run_conversation_streaming(agent):
    """
    流式对话循环 - 智能选择流式策略
    基础问题：直接使用 model.astream() 真流式
    工具问题：使用 Agent（虽然受限但能调用工具）
    """
    from langchain_community.chat_message_histories import ChatMessageHistory

    session_histories = {}

    def get_session_history(session_id: str):
        if session_id not in session_histories:
            session_histories[session_id] = ChatMessageHistory()
        return session_histories[session_id]

    session_id = "user_1"

    print("=" * 80)
    print("智能体已启动！输入 'exit' 或 'quit' 结束对话。")
    print("=" * 80 + "\n")

    while True:
        try:
            user_input = input("你: ")
        except EOFError:
            break

        if user_input.lower() in ["exit", "quit", "退出"]:
            print("\n对话已结束。")
            break

        if not user_input.strip():
            continue

        try:
            history = get_session_history(session_id)
            messages = history.messages + [HumanMessage(content=user_input)]

            use_tools = needs_tools(user_input)

            print("AI: ", end="", flush=True)

            full_response = ""
            metrics = PerformanceMetrics()
            metrics.record("request_start")

            use_tools = needs_tools(user_input)
            metrics.record("tool_detection")

            if use_tools:
                print("[思考中...] ", end="", flush=True)

                async for chunk in stream_agent_response(
                    agent, messages, history, user_input, metrics
                ):
                    print(chunk, end="", flush=True)
                    full_response += chunk
            else:
                print("[基础流式...] ")
                metrics.record("agent_start")
                chunk_count = 0
                async for chunk in stream_basic_response(messages, history, user_input):
                    if chunk_count == 0:
                        metrics.record("first_chunk")
                    metrics.record_chunk(chunk_count)
                    print(chunk, end="", flush=True)
                    full_response += chunk
                    chunk_count += 1
                metrics.record("last_chunk")

            metrics.record("response_end")
            print()

            # 打印详细性能报告
            metrics.print_detailed_report()

        except Exception as e:
            print(f"\n[ERROR] 处理请求时出错: {e}\n")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断程序")
    except Exception as e:
        print(f"\n[ERROR] 程序异常: {e}")
        import traceback

        traceback.print_exc()
