# -*- coding: utf-8 -*-
"""全局异常定义"""


class AgentException(Exception):
    """智能体基础异常"""

    def __init__(self, message: str, code: int = 1000):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ToolExecutionError(AgentException):
    """工具执行异常"""

    def __init__(self, tool_name: str, message: str):
        super().__init__(f"工具执行失败 [{tool_name}]: {message}", code=1001)


class IntentClassificationError(AgentException):
    """意图分类异常"""

    def __init__(self, message: str):
        super().__init__(f"意图分类失败: {message}", code=1002)


class ModelAPIError(AgentException):
    """模型 API 调用异常"""

    def __init__(self, message: str):
        super().__init__(f"模型 API 调用失败: {message}", code=1003)


class ConfigurationError(AgentException):
    """配置异常"""

    def __init__(self, message: str):
        super().__init__(f"配置错误: {message}", code=1004)
