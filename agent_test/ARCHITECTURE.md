# 解耦智能体架构设计说明

## 架构概述

本架构实现了一个**解耦的智能体系统**，通过小模型进行意图判断，决定使用工具调用还是直接对话，并包含完整的性能监控。

## 核心组件

### 1. 意图分类器 (IntentClassifier)
**职责**: 使用轻量级模型判断用户意图
**输入**: 用户输入文本
**输出**: IntentResult（意图类型、置信度、建议工具、提取参数）

```python
class IntentClassifier:
    async def classify(self, user_input: str) -> IntentResult
```

**系统提示词** (`INTENT_CLASSIFICATION_SYSTEM_PROMPT`):
- 定义了可用的工具列表
- 规定了三种意图类型：DIRECT_CHAT、TOOL_CALL、CLARIFICATION
- 要求返回JSON格式，包含置信度和推理过程

### 2. 工具执行器 (ToolExecutor)
**职责**: 执行具体的工具调用
**输入**: 工具名称和参数
**输出**: ToolCall（包含执行结果和耗时）

```python
class ToolExecutor:
    async def execute(self, tool_name: str, arguments: Dict) -> ToolCall
    async def execute_multiple(self, tool_calls: List[Dict]) -> List[ToolCall]
```

### 3. 主对话模型 (Main Model)
**职责**: 生成最终回复
**系统提示词** (`MAIN_MODEL_SYSTEM_PROMPT`):
- 说明可用的工具类型
- 规定工作原则（基于工具结果回答、简洁准确、中文回答）
- 定义工具结果格式

### 4. 性能监控 (PerformanceMetrics)
**职责**: 记录各阶段耗时
**监控阶段**:
1. start → intent_classified: 意图分类耗时
2. intent_classified → tools_executed: 工具执行耗时
3. tools_executed → response_generated: 回复生成耗时
4. response_generated → end: 历史更新耗时

## Message List 结构

### 标准消息格式

```python
# 系统消息
{
    "role": "system",
    "content": "系统提示词..."
}

# 用户消息 (HumanMessage)
{
    "role": "user", 
    "content": "用户输入..."
}

# AI消息 (AIMessage)
{
    "role": "assistant",
    "content": "AI回复...",
    "tool_calls": [  # 可选
        {
            "id": "call_1",
            "name": "tool_name",
            "arguments": {...}
        }
    ]
}

# 工具消息 (ToolMessage)
{
    "role": "tool",
    "tool_call_id": "call_1",
    "name": "tool_name",
    "content": "工具执行结果..."
}
```

### 消息构建流程

#### 1. 意图分类消息
```python
messages = [
    {"role": "system", "content": INTENT_CLASSIFICATION_SYSTEM_PROMPT},
    {"role": "user", "content": user_input}
]
```

#### 2. 主模型消息（带工具结果）
```python
messages = [
    {"role": "system", "content": MAIN_MODEL_SYSTEM_PROMPT},
    # ... 对话历史 ...
    {"role": "user", "content": """
        工具调用结果：
        
        [工具] get_weather_now
        [参数] {"location": "北京"}
        [结果] 温度: 25°C, 天气: 晴...
        
        用户问题：北京今天天气怎么样？
    """}
]
```

## 处理流程

```
用户输入
    ↓
[Stage 1] 意图分类 (小模型)
    ↓
判断意图类型
    ├─ DIRECT_CHAT ───→ [Stage 3] 主模型直接回复
    ├─ TOOL_CALL ─────→ [Stage 2] 执行工具
    │                       ↓
    │                  获取工具结果
    │                       ↓
    │               [Stage 3] 主模型基于工具结果回复
    └─ CLARIFICATION → 请求用户澄清
                            ↓
                    [Stage 4] 更新对话历史
                            ↓
                    返回 AgentResponse
```

## 解耦设计特点

### 1. 模型解耦
- **意图分类模型**: 轻量级（如 qwen2.5-7b）
  - 低温度（temperature=0.1）
  - 快速响应
  - 专门用于意图判断
  
- **主对话模型**: 大模型（如 qwen3-235b）
  - 正常温度（temperature=0.7）
  - 高质量生成
  - 负责最终回复

### 2. 组件解耦
每个组件职责单一，通过明确的数据结构交互：
- `IntentResult`: 意图分类结果
- `ToolCall`: 单次工具调用记录
- `AgentResponse`: 完整响应（包含所有信息）

### 3. 工具解耦
- 工具定义在 `Function_Call` 模块中
- 通过 `ALL_FUNCTIONS` 字典注入
- 支持动态添加/移除工具

## 性能监控

### 监控指标
```python
@dataclass
class PerformanceMetrics:
    stage_times: Dict[str, float]      # 各阶段时间戳
    stage_durations: Dict[str, float] # 各阶段耗时（毫秒）
```

### 输出示例
```
================================================================================
[性能监控报告]
================================================================================
  start_to_intent_classified: 245.32 ms
  intent_classified_to_tools_executed: 1234.56 ms
  tools_executed_to_response_generated: 987.65 ms
  response_generated_to_end: 12.34 ms
  总耗时: 2480.87 ms
================================================================================
```

## 使用示例

```python
# 初始化
agent = DecoupledAgent(
    intent_model=small_model,  # 轻量级模型
    main_model=large_model,    # 主模型
    tools=ALL_FUNCTIONS        # 工具函数字典
)

# 处理请求
response = await agent.process("北京今天天气怎么样？", stream=False)

# 获取结果
print(response.content)           # AI回复
print(response.intent)            # 意图类型
print(response.tool_calls)        # 工具调用记录
response.metrics.print_report()   # 性能报告
```

## 扩展性

### 添加新工具
1. 在 `Function_Call` 模块中实现工具函数
2. 在 `INTENT_CLASSIFICATION_SYSTEM_PROMPT` 中添加工具描述
3. 自动通过 `ALL_FUNCTIONS` 注入

### 添加新意图类型
1. 在 `IntentType` 枚举中添加新类型
2. 在 `DecoupledAgent.process()` 中添加处理逻辑

### 自定义性能监控
可以继承 `PerformanceMetrics` 类，添加自定义监控指标。

## 文件结构

```
agent_test/
├── decoupled_agent.py       # 主架构实现
├── agent_test.py           # 原MCP版本
└── ...

Function_Call/
├── __init__.py             # 导出 ALL_TOOLS, ALL_FUNCTIONS
├── Weather/
│   └── weather_tools.py    # 天气工具实现
└── Map/
    └── map_tools.py        # 地图工具实现
```

## 运行方式

```bash
cd agent_test
python decoupled_agent.py
```

需要确保：
1. 已安装依赖：`pip install httpx python-dotenv langchain langchain-openai`
2. 配置了 `.env` 文件（包含 API_KEY、HEFENG_KEY、BAIDU_MAP_AK）
