# AGENTS.md - Coding Guidelines for Agentic Agents

This document provides guidelines for AI agents working in the agent_test repository.

## Project Overview

This is a Python-based LangChain agent test project that integrates MCP (Model Context Protocol) services for weather and map queries. It uses streaming responses and session management for natural language interactions.

## Build, Test, and Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent
python agent_test.py

# Run individual MCP service tests
cd MCP/Weather && python test_weather.py
cd MCP/Map && python test_map.py

# Lint with ruff (if configured)
ruff check .
ruff check --fix .
```

## Code Style Guidelines

### Language and Comments

- **Primary Language**: Chinese for comments, docstrings, and user-facing messages
- **Code**: Python 3.10+ with type hints
- **Encoding**: UTF-8 (ensure files have `# -*- coding: utf-8 -*-` header)

### Imports

Order imports in three groups with blank lines between:

1. Standard library imports
2. Third-party package imports
3. Local module imports

```python
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pydantic import SecretStr

# Local imports at the bottom
from .config import load_config
```

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private functions**: `_leading_underscore`
- **Internal functions**: `_function_name` (for MCP tool wrappers)

### Type Hints

Always use type hints for function parameters and return values:

```python
def needs_tools(user_input: str) -> bool:
    """判断用户输入是否需要调用工具"""
    pass

async def stream_basic_response(
    messages: list, 
    session_history, 
    user_input: str
) -> AsyncGenerator[str, None]:
    """流式生成基础响应"""
    pass
```

### Error Handling

Use try/except with specific exceptions and Chinese error messages:

```python
try:
    result = await some_async_operation()
except ValueError as e:
    print(f"[ERROR] 无效的值: {e}")
    raise
except Exception as e:
    print(f"[ERROR] 处理请求时出错: {e}")
    import traceback
    traceback.print_exc()
```

### Async Patterns

- Use `async`/`await` for all I/O operations
- Use `async for` for streaming responses
- Use `asyncio.run()` in `if __name__ == "__main__"`
- Always close resources in `finally` blocks

```python
async def main():
    client = MultiServerMCPClient(server_config)
    try:
        tools = await client.get_tools()
        # ... use tools
    finally:
        if hasattr(client, "aclose"):
            await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
```

### MCP Service Integration

When creating MCP tools:

1. Separate business logic from MCP decorators:

```python
def _get_weather_now(location: str) -> str:
    """业务逻辑实现（私有函数）"""
    # Actual implementation
    pass

@mcp.tool()
def get_weather_now(location: str) -> str:
    """MCP工具入口（公开装饰器）"""
    return _get_weather_now(location)
```

2. Use `client.get_tools()` to maintain session lifecycle:

```python
# Correct - session stays open
client = MultiServerMCPClient(server_config)
all_tools = await client.get_tools()
agent = create_agent(model=model, tools=all_tools)

# Incorrect - session closes prematurely
async with client.session("server") as session:
    tools = await load_mcp_tools(session)
    # Session closed when exiting context
```

### Environment Variables

Load environment variables at module level:

```python
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BAIDU_MAP_AK = os.getenv("BAIDU_MAP_AK")
HEFENG_KEY = os.getenv("HEFENG_KEY")
HEFENG_API_HOST = os.getenv("HEFENG_API_HOST")
```

### Docstrings

Use Chinese docstrings with triple quotes:

```python
def needs_tools(user_input: str) -> bool:
    """
    判断用户输入是否需要调用工具
    
    基于关键词判断，简单问候和基础问题不需要工具
    
    Args:
        user_input: 用户输入文本
        
    Returns:
        bool: 是否需要工具
    """
    pass
```

### Logging and Output

Use consistent log prefixes:

- `[OK]` - Success
- `[ERROR]` - Error
- `[INFO]` - Information
- `[WARN]` - Warning

```python
print(f"[OK] 加载了 {len(tools)} 个工具")
print(f"[ERROR] 程序异常: {e}")
print("[INFO] 程序正常退出")
```

## Testing Guidelines

- Create test files as `test_<module>.py`
- Use print-based output for manual verification
- Import internal functions (prefixed with `_`) for testing
- Include Chinese comments in test descriptions

```python
def test_get_weather_now():
    """测试实时天气查询"""
    print("\n" + "=" * 60)
    print("测试 1: 实时天气 (get_weather_now)")
    print("=" * 60)
    # Test implementation
```

## Security Guidelines

- Never commit real API keys
- Use `.env` file for credentials
- Use `SecretStr` for API keys in Pydantic models
- MCP services should load their own `.env` files

## Common Tasks

### Adding a New MCP Tool

1. Add business logic as private function `_tool_name`
2. Create public decorated function `tool_name`
3. Update server configuration
4. Add test in `test_<service>.py`

### Running Single Test

```bash
python test_weather.py
```

### Environment Setup

Required environment variables in `.env`:

```env
API_KEY="your_langchain_api_key"
BAIDU_MAP_AK="your_baidu_map_key"
HEFENG_KEY="your_qweather_key"
HEFENG_API_HOST="your.qweatherapi.com"
```

## Project Structure

```
agent_test/
├── agent_test.py          # Main agent entry point
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── 测试文档.md             # Chinese documentation
MCP/
├── Map/
│   ├── server.py      # Baidu Map MCP service
│   └── test_map.py    # Map service tests
└── Weather/
    ├── server.py      # QWeather MCP service
    └── test_weather.py # Weather service tests
```

## Important Notes

1. **Session Management**: Always keep MCP sessions open during agent lifecycle
2. **Windows Encoding**: Avoid emoji characters; use `[xxx]` format instead
3. **API Host**: QWeather requires dedicated API host from 2026 onwards
4. **FastMCP 2.x**: Tool decorators wrap functions as FunctionTool objects
5. **Streaming**: Use `model.astream()` for true streaming, `agent.astream()` for tool calls
