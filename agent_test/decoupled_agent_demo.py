# -*- coding: utf-8 -*-
"""
解耦智能体架构 - 简化演示版（使用模拟数据）
展示完整的架构设计和性能监控
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum


# ==================== 数据类定义 ====================


class IntentType(Enum):
    """意图类型枚举"""

    DIRECT_CHAT = "direct_chat"
    TOOL_CALL = "tool_call"
    CLARIFICATION = "clarification"


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
            ) * 1000

    def print_report(self):
        """打印性能报告"""
        self.calculate_durations()
        print("\n" + "=" * 80)
        print("[性能监控报告]")
        print("=" * 80)
        for stage, duration in self.stage_durations.items():
            print(f"  {stage:40s}: {duration:>8.2f} ms")
        total = sum(self.stage_durations.values())
        print(f"  {'总计':40s}: {total:>8.2f} ms")
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

可用工具：
1. get_weather_now - 获取实时天气（参数: location）
2. get_weather_forecast - 获取天气预报（参数: location, days）
3. get_air_quality - 获取空气质量（参数: location）
4. geocode - 地址转坐标（参数: address）
5. place_search - 地点搜索（参数: query, region）
6. get_direction - 路线规划（参数: origin, destination, mode）

分类规则：
- DIRECT_CHAT: 问候、闲聊、简单问答、不需要实时数据
- TOOL_CALL: 需要天气、地图、位置、路线等实时信息
- CLARIFICATION: 用户意图不明确

请以JSON格式返回：
{
    "intent": "direct_chat|tool_call|clarification",
    "confidence": 0.95,
    "reasoning": "分类理由",
    "suggested_tools": ["tool_name"],
    "extracted_params": {"location": "北京"}
}"""


MAIN_MODEL_SYSTEM_PROMPT = """你是智能助手。根据工具结果回答用户问题。

工作原则：
1. 如果有工具结果，基于结果回答
2. 如果没有，直接回答
3. 简洁、准确、有帮助
4. 使用中文"""


# ==================== 模拟工具函数 ====================


def mock_get_weather_now(location: str) -> str:
    """模拟获取天气"""
    time.sleep(0.5)  # 模拟网络延迟
    return f"[位置] {location} 实时天气\n[温度] 25°C\n[天气] 晴\n[湿度] 45%"


def mock_get_weather_forecast(location: str, days: int = 3) -> str:
    """模拟获取天气预报"""
    time.sleep(0.5)
    return f"[位置] {location} {days}天天气预报\n今天: 晴 25°C\n明天: 多云 23°C\n后天: 阴 20°C"


def mock_geocode(address: str) -> str:
    """模拟地理编码"""
    time.sleep(0.3)
    return f"地址：{address}\n经度：116.4074\n纬度：39.9042"


def mock_place_search(query: str, region: str = "全国") -> str:
    """模拟地点搜索"""
    time.sleep(0.4)
    return f"搜索'{query}'在{region}:\n1. 测试地点A\n2. 测试地点B\n3. 测试地点C"


def mock_get_direction(origin: str, destination: str, mode: str = "driving") -> str:
    """模拟路线规划"""
    time.sleep(0.6)
    return f"从{origin}到{destination}（{mode}）:\n距离: 5.2公里\n预计时间: 15分钟"


# 工具函数字典
MOCK_TOOLS = {
    "get_weather_now": mock_get_weather_now,
    "get_weather_forecast": mock_get_weather_forecast,
    "geocode": mock_geocode,
    "place_search": mock_place_search,
    "get_direction": mock_get_direction,
}


# ==================== Message Builder ====================


class MessageBuilder:
    """消息构建器"""

    @staticmethod
    def create_system_message(content: str) -> Dict[str, str]:
        return {"role": "system", "content": content}

    @staticmethod
    def create_human_message(content: str) -> Dict[str, str]:
        return {"role": "user", "content": content}

    @staticmethod
    def create_ai_message(
        content: str, tool_calls: List[Dict] = None
    ) -> Dict[str, Any]:
        message = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return message

    @staticmethod
    def create_tool_message(
        tool_call_id: str, content: str, name: str
    ) -> Dict[str, str]:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content,
        }


# ==================== 模拟模型 ====================


class MockIntentModel:
    """模拟意图分类模型"""

    async def classify(self, user_input: str) -> Dict:
        """模拟意图分类"""
        await asyncio.sleep(0.2)  # 模拟推理时间

        user_input_lower = user_input.lower()

        # 简单关键词匹配
        if any(word in user_input_lower for word in ["天气", "温度", "下雨", "晴"]):
            return {
                "intent": "tool_call",
                "confidence": 0.95,
                "reasoning": "用户询问天气信息",
                "suggested_tools": ["get_weather_now"],
                "extracted_params": {"location": self._extract_location(user_input)},
            }
        elif any(
            word in user_input_lower for word in ["路线", "导航", "怎么走", "距离"]
        ):
            return {
                "intent": "tool_call",
                "confidence": 0.92,
                "reasoning": "用户询问路线信息",
                "suggested_tools": ["get_direction"],
                "extracted_params": {
                    "origin": self._extract_origin(user_input),
                    "destination": self._extract_destination(user_input),
                },
            }
        elif any(
            word in user_input_lower for word in ["位置", "坐标", "地址", "在哪里"]
        ):
            return {
                "intent": "tool_call",
                "confidence": 0.88,
                "reasoning": "用户询问位置信息",
                "suggested_tools": ["geocode"],
                "extracted_params": {"address": self._extract_location(user_input)},
            }
        elif any(word in user_input_lower for word in ["你好", "嗨", "hello", "hi"]):
            return {
                "intent": "direct_chat",
                "confidence": 0.98,
                "reasoning": "用户打招呼",
                "suggested_tools": [],
                "extracted_params": {},
            }
        else:
            return {
                "intent": "direct_chat",
                "confidence": 0.75,
                "reasoning": "一般性问题，直接回答",
                "suggested_tools": [],
                "extracted_params": {},
            }

    def _extract_location(self, text: str) -> str:
        """提取地点"""
        cities = [
            "北京",
            "上海",
            "广州",
            "深圳",
            "杭州",
            "南京",
            "合肥",
            "天津",
            "重庆",
        ]
        for city in cities:
            if city in text:
                return city
        return "北京"  # 默认

    def _extract_origin(self, text: str) -> str:
        """提取起点"""
        if "从" in text and "到" in text:
            return text.split("从")[1].split("到")[0].strip()
        return "天安门"

    def _extract_destination(self, text: str) -> str:
        """提取终点"""
        if "到" in text:
            parts = text.split("到")
            if len(parts) > 1:
                return parts[1].split("怎么")[0].split("走")[0].strip()
        return "故宫"


class MockMainModel:
    """模拟主模型"""

    async def generate(self, messages: List[Dict]) -> str:
        """模拟生成回复"""
        await asyncio.sleep(0.8)  # 模拟生成时间

        # 获取最后一条用户消息
        user_msg = ""
        tool_results = ""
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"]
                if "工具调用结果" in content:
                    tool_results = content
                else:
                    user_msg = content

        # 基于是否有工具结果生成回复
        if tool_results and "天气" in user_msg:
            return "根据查询结果，北京今天天气晴朗，温度25°C，湿度45%，适合外出活动！"
        elif tool_results and ("路线" in user_msg or "怎么走" in user_msg):
            return "从天安门到故宫大约5.2公里，驾车约15分钟。您可以选择：\n1. 长安街 -> 南池子大街\n2. 或者步行穿过天安门广场"
        elif tool_results and "坐标" in user_msg:
            return f"已为您查询到地址坐标：经度116.4074，纬度39.9042"
        elif "你好" in user_msg or "嗨" in user_msg:
            return "你好！我是智能助手，有什么可以帮助你的吗？"
        else:
            return f"我理解您的问题是关于：{user_msg[:20]}...\n这是一个很好的问题，我可以帮您解答。"


# ==================== 核心组件 ====================


class IntentClassifier:
    """意图分类器"""

    def __init__(self, model: MockIntentModel):
        self.model = model

    async def classify(self, user_input: str) -> IntentResult:
        """分类用户意图"""
        result = await self.model.classify(user_input)

        return IntentResult(
            intent=IntentType(result["intent"]),
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            suggested_tools=result.get("suggested_tools", []),
            extracted_params=result.get("extracted_params", {}),
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
                if asyncio.iscoroutinefunction(func):
                    result = await func(**arguments)
                else:
                    # 在异步环境中运行同步函数
                    result = await asyncio.to_thread(func, **arguments)
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
        tasks = []
        for tc in tool_calls:
            task = self.execute(tc["name"], tc.get("arguments", {}))
            tasks.append(task)

        return await asyncio.gather(*tasks)


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
        intent_model: MockIntentModel,
        main_model: MockMainModel,
        tools: Dict[str, Callable] = None,
    ):
        self.intent_classifier = IntentClassifier(intent_model)
        self.main_model = main_model
        self.tool_executor = ToolExecutor(tools or MOCK_TOOLS)
        self.conversation_history: List[Dict] = []
        self.message_builder = MessageBuilder()

    async def process(self, user_input: str) -> AgentResponse:
        """
        处理用户输入的主流程

        流程：
        1. 意图分类
        2. [可选] 工具执行
        3. 主模型生成回复
        4. 更新历史
        """
        metrics = PerformanceMetrics()
        metrics.record("start")

        print(f"\n{'=' * 80}")
        print(f"用户: {user_input}")
        print(f"{'=' * 80}")

        # ===== Stage 1: 意图分类 =====
        print("\n[Stage 1] 意图分类中...")
        intent_result = await self.intent_classifier.classify(user_input)
        metrics.record("intent_classified")

        print(f"[OK] 意图: {intent_result.intent.value}")
        print(f"    置信度: {intent_result.confidence:.2f}")
        print(f"    推理: {intent_result.reasoning}")
        if intent_result.suggested_tools:
            print(f"    建议工具: {intent_result.suggested_tools}")
        if intent_result.extracted_params:
            print(f"    提取参数: {intent_result.extracted_params}")

        tool_calls: List[ToolCall] = []

        # ===== Stage 2: 工具执行（如果需要）=====
        if intent_result.intent == IntentType.TOOL_CALL:
            print("\n[Stage 2] 执行工具...")

            tools_to_call = []
            for tool_name in intent_result.suggested_tools:
                if tool_name in MOCK_TOOLS:
                    tools_to_call.append(
                        {"name": tool_name, "arguments": intent_result.extracted_params}
                    )

            if tools_to_call:
                tool_calls = await self.tool_executor.execute_multiple(tools_to_call)
                metrics.record("tools_executed")

                print(f"[OK] 执行了 {len(tool_calls)} 个工具:")
                for tc in tool_calls:
                    print(f"    - {tc.tool_name}: {tc.duration_ms:.2f} ms")
                    print(f"      参数: {tc.arguments}")
                    print(f"      结果: {tc.result[:100]}...")
            else:
                print("[WARN] 没有可用的工具")

        # ===== Stage 3: 主模型生成回复 =====
        print("\n[Stage 3] 生成回复...")

        # 构建消息列表
        messages = [
            self.message_builder.create_system_message(MAIN_MODEL_SYSTEM_PROMPT)
        ]
        messages.extend(self.conversation_history)

        # 如果有工具结果，添加到上下文
        if tool_calls:
            tool_context = "工具调用结果：\n\n"
            for tc in tool_calls:
                tool_context += f"[工具] {tc.tool_name}\n"
                tool_context += (
                    f"[参数] {json.dumps(tc.arguments, ensure_ascii=False)}\n"
                )
                tool_context += f"[结果] {tc.result}\n\n"

            messages.append(
                self.message_builder.create_human_message(
                    f"{tool_context}\n用户问题：{user_input}"
                )
            )
        else:
            messages.append(self.message_builder.create_human_message(user_input))

        print(f"[INFO] Message List 结构:")
        for i, msg in enumerate(messages):
            role = msg["role"]
            content_preview = (
                msg["content"][:50] + "..."
                if len(msg["content"]) > 50
                else msg["content"]
            )
            print(f"    [{i}] {role}: {content_preview}")

        content = await self.main_model.generate(messages)
        metrics.record("response_generated")

        # ===== Stage 4: 更新历史 =====
        self._update_history(user_input, content, tool_calls)
        metrics.record("end")

        print(f"\n[OK] AI: {content}")

        # 打印性能报告
        metrics.print_report()

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
        """更新对话历史"""
        # 添加用户消息
        self.conversation_history.append(
            self.message_builder.create_human_message(user_input)
        )

        # 如果有工具调用，添加工具消息
        if tool_calls:
            for i, tc in enumerate(tool_calls):
                self.conversation_history.append(
                    self.message_builder.create_tool_message(
                        tool_call_id=f"call_{i}", content=tc.result, name=tc.tool_name
                    )
                )

        # 添加AI回复
        self.conversation_history.append(
            self.message_builder.create_ai_message(response)
        )

        # 限制历史长度（保留最近10轮）
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]


# ==================== 演示 ====================


async def demo():
    """演示解耦智能体"""

    print("=" * 80)
    print("解耦智能体架构演示")
    print("=" * 80)
    print("\n架构特点：")
    print("  1. 小模型进行意图分类（模拟）")
    print("  2. 解耦的工具调用")
    print("  3. 大模型生成回复（模拟）")
    print("  4. 完整的性能监控")
    print("  5. 清晰的Message List结构")
    print("\n" + "=" * 80)

    # 创建模拟模型
    intent_model = MockIntentModel()
    main_model = MockMainModel()

    # 创建智能体
    agent = DecoupledAgent(
        intent_model=intent_model, main_model=main_model, tools=MOCK_TOOLS
    )

    # 测试用例
    test_cases = [
        "你好，我是新来的用户",  # DIRECT_CHAT
        "北京今天天气怎么样？",  # TOOL_CALL - weather
        "从天安门到故宫怎么走？",  # TOOL_CALL - direction
        "北京市天安门广场的坐标是多少？",  # TOOL_CALL - geocode
        "谢谢你的帮助！",  # DIRECT_CHAT
    ]

    print("\n开始测试...\n")

    for i, user_input in enumerate(test_cases, 1):
        print(f"\n{'#' * 80}")
        print(f"# 测试 {i}/{len(test_cases)}")
        print(f"{'#' * 80}")

        response = await agent.process(user_input)

        await asyncio.sleep(1)  # 测试间隔

    print(f"\n{'=' * 80}")
    print("测试完成！")
    print(f"{'=' * 80}")

    # 打印最终的对话历史
    print("\n[最终对话历史 - Message List 结构]")
    print("=" * 80)
    for i, msg in enumerate(agent.conversation_history):
        role = msg["role"]
        content = (
            msg["content"][:100] + "..."
            if len(msg["content"]) > 100
            else msg["content"]
        )
        print(f"\n[{i}] Role: {role}")
        print(f"    Content: {content}")
        if "tool_calls" in msg:
            print(f"    Tool Calls: {msg['tool_calls']}")
        if "tool_call_id" in msg:
            print(f"    Tool Call ID: {msg['tool_call_id']}")
            print(f"    Name: {msg['name']}")


if __name__ == "__main__":
    asyncio.run(demo())
