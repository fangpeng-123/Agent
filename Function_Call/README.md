# Function Call 工具集

本项目将MCP工具转换为OpenAI Function Call格式，可直接用于LLM的函数调用场景。

## 目录结构

```
Function_Call/
├── __init__.py           # 主包初始化
├── agent_demo.py         # 整合使用示例
├── Weather/              # 和风天气工具
│   ├── __init__.py
│   ├── weather_tools.py  # 天气功能实现
│   └── example_usage.py  # 使用示例
└── Map/                  # 百度地图工具
    ├── __init__.py
    ├── map_tools.py      # 地图功能实现
    └── example_usage.py  # 使用示例
```

## 快速开始

### 1. 环境配置

确保在项目根目录或工具目录中创建 `.env` 文件：

```env
# 和风天气API配置
HEFENG_KEY="your_qweather_key"
HEFENG_API_HOST="your.qweatherapi.com"

# 百度地图API配置
BAIDU_MAP_AK="your_baidu_map_key"
```

### 2. 基本使用

#### 方式一：直接导入函数

```python
from Function_Call import (
    get_weather_now,
    get_weather_forecast,
    geocode,
    place_search,
)

# 查询天气
result = get_weather_now("北京")
print(result)

# 地理编码
result = geocode("北京市天安门")
print(result)
```

#### 方式二：使用工具定义（Function Call场景）

```python
from Function_Call import ALL_TOOLS, ALL_FUNCTIONS
import json

# 获取所有工具定义
tools = ALL_TOOLS

# 模拟LLM返回的工具调用
function_name = "get_weather_now"
arguments = {"location": "北京"}

# 执行工具调用
if function_name in ALL_FUNCTIONS:
    result = ALL_FUNCTIONS[function_name](**arguments)
    print(result)
```

### 3. 与OpenAI集成

```python
from openai import OpenAI
from Function_Call import ALL_TOOLS, ALL_FUNCTIONS
import json

client = OpenAI(api_key="your-openai-api-key")

# 发送消息和工具定义
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
    tools=ALL_TOOLS,
    tool_choice="auto"
)

# 处理工具调用
message = response.choices[0].message
if message.tool_calls:
    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    # 执行工具
    result = ALL_FUNCTIONS[function_name](**arguments)
    
    # 将结果返回给LLM
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "北京今天天气怎么样？"},
            message,
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            }
        ]
    )
    
    print(response.choices[0].message.content)
```

### 4. 与LangChain集成

```python
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from Function_Call import ALL_FUNCTIONS

# 创建工具列表
tools = [
    Tool(
        name="get_weather_now",
        func=ALL_FUNCTIONS["get_weather_now"],
        description="获取指定城市的实时天气情况"
    ),
    Tool(
        name="geocode",
        func=ALL_FUNCTIONS["geocode"],
        description="将地址转换为经纬度坐标"
    ),
    # ... 其他工具
]

# 初始化Agent
llm = ChatOpenAI(model="gpt-4")
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="openai-functions",
    verbose=True
)

# 使用Agent
result = agent.run("北京今天天气怎么样？")
print(result)
```

## 可用工具列表

### 天气工具

| 工具名 | 功能描述 |
|--------|----------|
| `get_weather_now` | 获取实时天气 |
| `get_weather_forecast` | 获取天气预报（3/7/10/15/30天） |
| `get_hourly_forecast` | 获取逐小时预报（24/72小时） |
| `get_air_quality` | 获取空气质量 |
| `get_life_index` | 获取生活指数 |
| `search_city` | 搜索城市信息 |

### 地图工具

| 工具名 | 功能描述 |
|--------|----------|
| `geocode` | 地理编码（地址转坐标） |
| `reverse_geocode` | 逆地理编码（坐标转地址） |
| `place_search` | 地点检索（POI搜索） |
| `get_direction` | 路线规划（驾车/步行/骑行/公交） |
| `get_ip_location` | IP定位 |

## 运行示例

```bash
# 运行整合示例
python agent_demo.py

# 运行天气工具示例
python Weather/example_usage.py

# 运行地图工具示例
python Map/example_usage.py

# 单独测试工具
python Weather/weather_tools.py
python Map/map_tools.py
```

## 工具定义格式

每个工具都遵循OpenAI Function Call格式：

```json
{
    "type": "function",
    "function": {
        "name": "get_weather_now",
        "description": "获取指定城市的实时天气情况",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称或LocationID"
                }
            },
            "required": ["location"]
        }
    }
}
```

## 注意事项

1. **环境变量**：确保正确配置API密钥
2. **网络连接**：工具需要访问互联网获取数据
3. **API限制**：注意各API的调用频率限制
4. **错误处理**：建议在实际使用时添加错误处理逻辑

## 依赖

```
httpx>=0.25.0
python-dotenv>=1.0.0
```

安装依赖：

```bash
pip install httpx python-dotenv
```
