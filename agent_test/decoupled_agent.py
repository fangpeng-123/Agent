# -*- coding: utf-8 -*-
"""
解耦智能体架构设计
包含意图路由、工具调用、性能监控的完整实现
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class IntentType(Enum):
    """意图类型枚举"""

    DIRECT_CHAT = "direct_chat"  # 直接对话
    TOOL_CALL = "tool_call"  # 需要调用工具
    CLARIFICATION = "clarification"  # 需要澄清


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    stage_times: Dict[str, float] = field(default_factory=dict)
    stage_durations: Dict[str, float] = field(default_factory=dict)

    def record(self, stage: str):
        """记录阶段时间戳"""
        self.stage_times[stage] = time.time()

    def calculate_durations(self):
        """计算各阶段耗时"""
        stages = list(self.stage_times.keys())
        for i in range(len(stages) - 1):
            start, end = stages[i], stages[i + 1]
            self.stage_durations[f"{start}_to_{end}"] = (
                self.stage_times[end] - self.stage_times[start]
            ) * 1000  # 转换为毫秒

    def print_report(self):
        """打印性能报告"""
        self.calculate_durations()
        print("\n" + "=" * 80)
        print("[性能监控报告]")
        print("=" * 80)
        for stage, duration in self.stage_durations.items():
            print(f"  {stage}: {duration:.2f} ms")
        total = sum(self.stage_durations.values())
        print(f"  总耗时: {total:.2f} ms")
        print("=" * 80)


@dataclass
class IntentResult:
    """意图识别结果"""

    intent: IntentType
    confidence: float
    reasoning: str
    suggested_tools: List[str] = field(default_factory=list)
    extracted_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """工具调用记录"""

    tool_name: str
    arguments: Dict[str, Any]
    result: str
    start_time: float
    end_time: float

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000


@dataclass
class AgentResponse:
    """智能体响应"""

    content: str
    intent: IntentType
    tool_calls: List[ToolCall] = field(default_factory=list)
    metrics: Optional[PerformanceMetrics] = None
    message_history: List[Dict] = field(default_factory=list)


# ==================== 系统提示词定义 ====================

INTENT_CLASSIFICATION_SYSTEM_PROMPT = """你是意图分类专家。分析用户输入，判断是否需要调用工具。

工具列表：
1. get_weather_now - 获取实时天气
2. get_weather_forecast - 获取天气预报
3. get_air_quality - 获取空气质量
4. geocode - 地址转坐标
5. place_search - 地点搜索
6. get_direction - 路线规划

分类规则：
- DIRECT_CHAT: 问候、闲聊、简单问答、不需要实时数据的问题
- TOOL_CALL: 需要天气、地图、位置、路线等实时信息
- CLARIFICATION: 用户意图不明确，需要澄清

请以JSON格式返回：
{
    "intent": "direct_chat|tool_call|clarification",
    "confidence": 0.95,
    "reasoning": "分类理由",
    "suggested_tools": ["tool_name1", "tool_name2"],
    "extracted_params": {
        "location": "提取的地点",
        "query": "提取的查询词"
    }
}"""


MAIN_MODEL_SYSTEM_PROMPT = """你是智能助手，帮助用户解答问题。

可用工具：
- 天气工具：获取实时天气、天气预报、空气质量
- 地图工具：地理编码、地点搜索、路线规划

工作原则：
1. 如果提供了工具调用结果，请基于结果回答用户问题
2. 如果没有工具结果，请直接回答
3. 回答要简洁、准确、有帮助
4. 使用中文回答

工具调用结果格式：
[工具名] 参数: {...}
结果: ...

请根据以上信息回答用户。"""


TOOL_RESULT_SUMMARY_PROMPT = """请根据工具调用结果，生成简洁的回答。

工具调用信息：
{tool_calls}

用户问题：{user_input}

要求：
1. 整合所有工具结果
2. 直接回答用户问题
3. 如有多个结果，分点说明
4. 使用中文"""


# ==================== Message List 结构定义 ====================


class MessageBuilder:
    """消息构建器 - 定义标准的message list结构"""

    @staticmethod
    def create_system_message(content: str) -> Dict[str, str]:
        """创建系统消息"""
        return {"role": "system", "content": content}

    @staticmethod
    def create_human_message(content: str) -> Dict[str, str]:
        """创建用户消息"""
        return {"role": "user", "content": content}

    @staticmethod
    def create_ai_message(
        content: str, tool_calls: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """创建AI消息"""
        message = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return message

    @staticmethod
    def create_tool_message(
        tool_call_id: str, content: str, name: str
    ) -> Dict[str, str]:
        """创建工具消息"""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content,
        }

    @staticmethod
    def build_intent_classification_messages(user_input: str) -> List[Dict]:
        """构建意图分类的消息列表"""
        return [
            MessageBuilder.create_system_message(INTENT_CLASSIFICATION_SYSTEM_PROMPT),
            MessageBuilder.create_human_message(user_input),
        ]

    @staticmethod
    def build_main_model_messages(
        user_input: str,
        tool_results: List[ToolCall],
        conversation_history: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """构建主模型的消息列表"""
        messages = [MessageBuilder.create_system_message(MAIN_MODEL_SYSTEM_PROMPT)]

        # 添加对话历史
        if conversation_history:
            messages.extend(conversation_history)

        # 如果有工具结果，添加到上下文
        if tool_results:
            tool_context = "工具调用结果：\n\n"
            for tc in tool_results:
                tool_context += f"[工具] {tc.tool_name}\n"
                tool_context += (
                    f"[参数] {json.dumps(tc.arguments, ensure_ascii=False)}\n"
                )
                tool_context += f"[结果] {tc.result}\n\n"

            messages.append(
                MessageBuilder.create_human_message(
                    f"{tool_context}\n用户问题：{user_input}"
                )
            )
        else:
            messages.append(MessageBuilder.create_human_message(user_input))

        return messages


# ==================== 工具定义导入 ====================

import sys
from pathlib import Path

# 添加 Function_Call 的父目录到路径（这样 Function_Call 才能作为包被导入）
agent_root = Path(__file__).parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

try:
    from Function_Call import ALL_TOOLS, ALL_FUNCTIONS

    print(f"[OK] 成功加载 {len(ALL_TOOLS)} 个工具")
except ImportError as e:
    print(f"[ERROR] 加载工具失败: {e}")
    print(f"       尝试从: {agent_root}")
    print(f"       sys.path: {sys.path[:3]}...")  # 只显示前3个路径
    ALL_TOOLS = []
    ALL_FUNCTIONS = {}


# ==================== 核心组件类 ====================


class IntentClassifier:
    """意图分类器 - 使用轻量级模型"""

    def __init__(self, model):
        self.model = model

    async def classify(self, user_input: str) -> IntentResult:
        """分类用户意图"""
        messages = MessageBuilder.build_intent_classification_messages(user_input)

        # 这里使用轻量级模型进行意图分类
        response = await self.model.ainvoke(messages)

        try:
            # 解析JSON响应
            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            # 提取JSON部分
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())

            return IntentResult(
                intent=IntentType(result.get("intent", "direct_chat")),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                suggested_tools=result.get("suggested_tools", []),
                extracted_params=result.get("extracted_params", {}),
            )
        except Exception as e:
            print(f"[WARN] 意图解析失败: {e}, 使用默认意图")
            return IntentResult(
                intent=IntentType.DIRECT_CHAT,
                confidence=0.5,
                reasoning="解析失败，默认直接对话",
            )


class ToolExecutor:
    """工具执行器"""

    def __init__(self, functions: Dict[str, Callable]):
        self.functions = functions

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCall:
        """执行单个工具"""
        start_time = time.time()

        if tool_name not in self.functions:
            result = f"[ERROR] 未找到工具: {tool_name}"
        else:
            try:
                func = self.functions[tool_name]
                # 支持同步和异步函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(**arguments)
                else:
                    result = func(**arguments)
            except Exception as e:
                result = f"[ERROR] 工具执行失败: {str(e)}"

        end_time = time.time()

        return ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            start_time=start_time,
            end_time=end_time,
        )

    async def execute_multiple(self, tool_calls: List[Dict]) -> List[ToolCall]:
        """批量执行工具"""
        results = []
        for tc in tool_calls:
            result = await self.execute(tc["name"], tc.get("arguments", {}))
            results.append(result)
        return results


class DecoupledAgent:
    """
    解耦智能体 - 核心协调器

    架构组件：
    1. IntentClassifier - 意图分类（小模型）
    2. ToolExecutor - 工具执行
    3. MainModel - 主模型生成回复
    4. PerformanceMetrics - 性能监控
    """

    def __init__(
        self,
        intent_model,  # 轻量级意图分类模型
        main_model,  # 主对话模型
        tools: Optional[Dict[str, Callable]] = None,
    ):
        self.intent_classifier = IntentClassifier(intent_model)
        self.main_model = main_model
        self.tool_executor = ToolExecutor(tools or ALL_FUNCTIONS)
        self.conversation_history: List[Dict] = []

    async def process(self, user_input: str, stream: bool = False) -> AgentResponse:
        """
        处理用户输入的主流程

        流程：
        1. 意图分类（轻量级模型）
        2. [可选] 工具执行
        3. 主模型生成回复
        4. 返回完整响应
        """
        metrics = PerformanceMetrics()
        metrics.record("start")

        # ===== Stage 1: 意图分类 =====
        print("[Stage 1] 意图分类中...")
        intent_result = await self.intent_classifier.classify(user_input)
        metrics.record("intent_classified")
        print(
            f"[OK] 意图: {intent_result.intent.value}, "
            f"置信度: {intent_result.confidence:.2f}"
        )
        print(f"    推理: {intent_result.reasoning}")
        if intent_result.suggested_tools:
            print(f"    建议工具: {intent_result.suggested_tools}")

        tool_calls: List[ToolCall] = []

        # ===== Stage 2: 工具执行（如果需要）=====
        if intent_result.intent == IntentType.TOOL_CALL:
            print("[Stage 2] 执行工具...")

            # 构建工具调用列表
            tools_to_call = []
            for tool_name in intent_result.suggested_tools:
                if tool_name in ALL_FUNCTIONS:
                    tools_to_call.append(
                        {"name": tool_name, "arguments": intent_result.extracted_params}
                    )

            if tools_to_call:
                tool_calls = await self.tool_executor.execute_multiple(tools_to_call)
                metrics.record("tools_executed")

                print(f"[OK] 执行了 {len(tool_calls)} 个工具:")
                for tc in tool_calls:
                    print(f"    - {tc.tool_name}: {tc.duration_ms:.2f} ms")
            else:
                print("[WARN] 没有可用的工具")

        # ===== Stage 3: 主模型生成回复 =====
        print("[Stage 3] 生成回复...")
        messages = MessageBuilder.build_main_model_messages(
            user_input, tool_calls, self.conversation_history
        )

        if stream:
            content = ""
            async for chunk in self.main_model.astream(messages):
                text = chunk.content if hasattr(chunk, "content") else str(chunk)
                content += text
                print(text, end="", flush=True)
        else:
            response = await self.main_model.ainvoke(messages)
            content = (
                response.content if hasattr(response, "content") else str(response)
            )

        metrics.record("response_generated")

        # ===== Stage 4: 更新历史 =====
        self._update_history(user_input, content, tool_calls)
        metrics.record("end")

        # 返回完整响应
        return AgentResponse(
            content=content,
            intent=intent_result.intent,
            tool_calls=tool_calls,
            metrics=metrics,
            message_history=self.conversation_history.copy(),
        )

    def _update_history(
        self, user_input: str, response: str, tool_calls: List[ToolCall]
    ):
        """更新对话历史

        注意：在我们的解耦架构中，工具调用由代码直接执行，不由模型触发。
        因此不在历史中添加 tool 消息，避免 OpenAI API 格式错误。
        工具结果通过当前轮次的上下文传递给主模型。
        """
        # 添加用户消息
        self.conversation_history.append(
            MessageBuilder.create_human_message(user_input)
        )

        # 添加AI回复（不包含 tool_calls，因为我们的工具调用不在模型内）
        self.conversation_history.append(MessageBuilder.create_ai_message(response))

        # 限制历史长度（保留最近10轮对话 = 20条消息）
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]


# ==================== 使用示例 ====================


async def example_usage():
    """使用示例"""
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr
    import os
    from dotenv import load_dotenv

    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    # 小模型 - 用于意图分类
    intent_model = ChatOpenAI(
        model="qwen2.5-7b-instruct",  # 轻量级模型
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(API_KEY) if API_KEY else None,
        temperature=0.1,  # 低温度，更确定性
    )

    # 大模型 - 用于主对话
    main_model = ChatOpenAI(
        model="qwen3-235b-a22b",  # 主模型
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(API_KEY) if API_KEY else None,
        temperature=0.7,
        streaming=True,
    )

    # 创建智能体
    agent = DecoupledAgent(
        intent_model=intent_model, main_model=main_model, tools=ALL_FUNCTIONS
    )

    # 测试对话
    test_inputs = [
        # "你好，今天天气怎么样？",  # 应该触发工具
        # "北京今天的温度是多少？",  # 应该触发工具
        # "讲个笑话",  # 应该直接对话
        # "从天安门到故宫怎么走？",  # 应该触发工具
        "北京今天要下雨吗？",  # 应该触发工具
    ]

    for user_input in test_inputs:
        print("\n" + "=" * 80)
        print(f"用户: {user_input}")
        print("=" * 80)

        response = await agent.process(user_input, stream=False)

        print(f"\nAI: {response.content}")
        print(f"\n意图: {response.intent.value}")

        if response.tool_calls:
            print(f"\n工具调用:")
            for tc in response.tool_calls:
                print(f"  - {tc.tool_name}: {tc.duration_ms:.2f} ms")

        # 打印性能报告
        if response.metrics:
            response.metrics.print_report()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
