# -*- coding: utf-8 -*-
"""告警机制"""

from typing import Callable, Dict, List


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.alerts: List[Dict] = []
        self.rules: Dict[str, Dict] = {}
        self.handlers: Dict[str, List[Callable]] = {}

    def add_rule(self, name: str, condition: Callable, threshold: float):
        """添加规则"""
        self.rules[name] = {"condition": condition, "threshold": threshold}

    def register_handler(self, alert_type: str, handler: Callable):
        """注册处理器"""
        if alert_type not in self.handlers:
            self.handlers[alert_type] = []
        self.handlers[alert_type].append(handler)

    def check(self, metric_name: str, value: float):
        """检查指标"""
        if metric_name in self.rules:
            rule = self.rules[metric_name]
            if rule["condition"](value, rule["threshold"]):
                self.trigger_alert(metric_name, value)

    def trigger_alert(self, metric_name: str, value: float):
        """触发告警"""
        alert = {
            "metric": metric_name,
            "value": value,
            "time": "now",
        }
        self.alerts.append(alert)

        alert_type = f"alert_{metric_name}"
        if alert_type in self.handlers:
            for handler in self.handlers[alert_type]:
                handler(alert)

    def get_active_alerts(self) -> List[Dict]:
        """获取活跃告警"""
        return self.alerts

    def clear_alerts(self):
        """清空告警"""
        self.alerts.clear()
