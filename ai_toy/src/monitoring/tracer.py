# -*- coding: utf-8 -*-
"""分布式追踪"""

import uuid
from typing import Dict, Optional


class Tracer:
    """分布式追踪器"""

    def __init__(self, service_name: str = "agent"):
        self.service_name = service_name
        self.spans: Dict[str, Dict] = {}

    def start_span(self, operation_name: str, parent_id: Optional[str] = None) -> str:
        """开始追踪"""
        span_id = str(uuid.uuid4())[:8]
        self.spans[span_id] = {
            "operation": operation_name,
            "parent_id": parent_id,
            "start_time": None,
            "end_time": None,
            "tags": {},
            "logs": [],
        }
        return span_id

    def end_span(self, span_id: str):
        """结束追踪"""
        if span_id in self.spans:
            self.spans[span_id]["end_time"] = "now"

    def add_tag(self, span_id: str, key: str, value: str):
        """添加标签"""
        if span_id in self.spans:
            self.spans[span_id]["tags"][key] = value

    def add_log(self, span_id: str, message: str):
        """添加日志"""
        if span_id in self.spans:
            self.spans[span_id]["logs"].append(message)

    def get_trace(self, span_id: str) -> Dict:
        """获取追踪"""
        return self.spans.get(span_id, {})
