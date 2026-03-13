# -*- coding: utf-8 -*-
"""性能监控模块"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class IntentResult:
    """意图识别结果"""

    intent: Any
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
    intent: Any
    tool_calls: List[ToolCall] = field(default_factory=list)
    metrics: Optional["PerformanceMetrics"] = None
    message_history: List[Dict] = field(default_factory=list)
    tts_result: Optional[object] = None


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    stage_times: Dict[str, float] = field(default_factory=dict)
    stage_durations: Dict[str, float] = field(default_factory=dict)
    first_token_time: Optional[float] = None
    first_audio_time: Optional[float] = None
    tools_loaded_time: Optional[float] = None
    program_start_time: Optional[float] = None
    tts_time: Optional[float] = None
    # 记录用户提问结束时间点（用于计算对话响应总耗时）
    user_input_end_time: Optional[float] = None

    def record(self, stage: str):
        self.stage_times[stage] = time.time()

    def set_first_token_time(self, first_token_ms: float):
        self.first_token_time = first_token_ms

    def set_first_audio_time(self, first_audio_ms: float):
        self.first_audio_time = first_audio_ms

    def set_tools_loaded_time(self, load_time: float):
        self.tools_loaded_time = load_time

    def set_program_start_time(self, start_time: float):
        self.program_start_time = start_time

    def set_tts_time(self, tts_ms: float):
        self.tts_time = tts_ms

    def set_user_input_end_time(self, end_time: float):
        """设置用户提问结束时间点"""
        self.user_input_end_time = end_time

    def calculate_durations(self):
        stages = list(self.stage_times.keys())
        for i in range(len(stages) - 1):
            start, end = stages[i], stages[i + 1]
            self.stage_durations[f"{start}_to_{end}"] = (
                self.stage_times[end] - self.stage_times[start]
            ) * 1000

    def print_report(self, include_tools_loaded: bool = False):
        self.calculate_durations()
        print("\n" + "=" * 80)
        print("[性能监控报告]")
        print("=" * 80)

        # 计算总耗时（从用户提问结束到语音回复结束）
        if self.user_input_end_time is not None:
            total_response_time = time.time() - self.user_input_end_time
            print(f"  对话响应总耗时: {total_response_time:.2f} s")

        if include_tools_loaded and self.tools_loaded_time is not None:
            print(f"  工具加载耗时: {self.tools_loaded_time / 1000:.2f} s")

        for stage, duration in self.stage_durations.items():
            print(f"  {stage}: {duration / 1000:.2f} s")
        if self.first_token_time is not None:
            print(f"  TTFT(首token延迟): {self.first_token_time / 1000:.2f} s")
        if self.first_audio_time is not None:
            print(f"  TTFA(首段音频延迟): {self.first_audio_time / 1000:.2f} s")
        if self.tts_time is not None:
            print(f"  TTS语音合成耗时: {self.tts_time / 1000:.2f} s")

        total = sum(self.stage_durations.values())
        if self.program_start_time is not None:
            program_total = time.time() - self.program_start_time
            print(f"  启动到回答完毕总耗时: {program_total:.2f} s")
        else:
            print(f"  总耗时: {total / 1000:.2f} s")
        print("=" * 80)
