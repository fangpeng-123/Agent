# -*- coding: utf-8 -*-
"""性能指标收集"""

from typing import Dict
import time


class MetricsCollector:
    """性能指标收集器"""

    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = {}

    def increment(self, name: str, value: int = 1):
        """增加计数器"""
        self.counters[name] = self.counters.get(name, 0) + value

    def gauge(self, name: str, value: float):
        """设置仪表值"""
        self.gauges[name] = value

    def histogram(self, name: str, value: float):
        """记录直方图"""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)

    def record_latency(self, operation: str, duration_ms: float):
        """记录延迟"""
        self.histogram(f"latency_{operation}", duration_ms)

    def get_summary(self) -> Dict:
        """获取摘要"""
        return {
            "counters": self.counters,
            "gauges": self.gauges,
            "histograms": {
                k: {"count": len(v), "avg": sum(v) / len(v)}
                for k, v in self.histograms.items()
            },
        }
