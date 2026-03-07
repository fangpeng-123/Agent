# 架构设计文档

## 系统架构

```
用户请求
    ↓
API 层 (FastAPI)
    ↓
智能体核心 (DecoupledAgent)
    ├── 意图分类 (Intent Classification)
    ├── 工具执行 (Tool Execution)
    └── 回复生成 (Response Generation)
    ↓
外部服务
    ├── 天气 API
    ├── 地图 API
    └── LLM API
```

## 模块职责

| 模块 | 职责 |
|------|------|
| src/agent_core.py | 核心智能体逻辑 |
| src/intent_classification.py | 意图识别 |
| src/tool_executor.py | 工具执行 |
| src/message_builder.py | 消息构建 |

## 数据流

1. 用户输入 → API 层
2. 意图分类 → 确定工具
3. 工具执行 → 获取数据
4. LLM 生成 → 回复用户
