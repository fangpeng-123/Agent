# AGENTS.md - Coding Guidelines for MCP Directory

This document provides guidelines for AI agents working in the MCP directory.

## Project Overview

The MCP directory contains Model Context Protocol (MCP) services:
- **Map/** - Baidu Map MCP service (Python)
- **Weather/** - QWeather MCP service (Python)
- **openclaw-map-mcp/** - TypeScript-based OpenClaw Map MCP extension

MCP services provide tools for LangChain agents via stdio transport.

## Build, Test, and Development Commands

### Python MCP Services

```bash
# Install dependencies
cd Map && pip install -r requirements.txt
cd Weather && pip install -r requirements.txt

# Run MCP service directly
python server.py

# Run tests
python test_map.py
python test_weather.py

# Lint with ruff (if configured)
ruff check .
ruff format .
```

### TypeScript OpenClaw Extension

```bash
cd openclaw-map-mcp

# Install dependencies
npm install

# Build
npm run build

# Type check
npx tsc --noEmit
```

## Code Style Guidelines

### Python MCP Services

#### Language and Comments

- **Primary Language**: Chinese for comments, docstrings, and user-facing messages
- **Code**: Python 3.10+ with type hints
- **Encoding**: UTF-8 (files should have `# -*- coding: utf-8 -*-` header)

#### FastMCP 2.x Pattern

Separate business logic from MCP decorators:

```python
# Internal function (business logic)
def _get_weather_now(location: str) -> str:
    """实时天气：业务逻辑实现（私有函数）"""
    if not HEFENG_KEY:
        return "错误：未配置密钥"
    # Implementation...

# Public decorated function (MCP tool)
@mcp.tool()
def get_weather_now(location: str) -> str:
    """
    实时天气：获取指定城市的实时天气情况
    
    Args:
        location: 城市名称或LocationID
        
    Returns:
        实时天气信息
    """
    return _get_weather_now(location)
```

#### Imports

Order: Standard library → Third-party → Local

```python
import os
import httpx
from pathlib import Path

from fastmcp import FastMCP
from dotenv import load_dotenv
```

#### Type Hints

Always use type hints:

```python
def geocode(address: str) -> str:
def _search_city(city_name: str, country: str = "CN") -> str:
```

#### Error Handling

Return Chinese error messages as strings (not exceptions):

```python
try:
    response = httpx.get(url, params=params, timeout=10)
    data = response.json()
    
    if data.get("status") == 0:
        return format_result(data)
    else:
        return f"查询失败：{data.get('msg', '未知错误')}"
except Exception as e:
    return f"请求异常：{str(e)}"
```

#### Environment Variables

Load from multiple locations with fallback:

```python
mcp_env_path = Path(__file__).parent / ".env"
agent_test_env_path = Path(__file__).parent.parent.parent / "agent_test" / ".env"

if mcp_env_path.exists():
    load_dotenv(mcp_env_path)
elif agent_test_env_path.exists():
    load_dotenv(agent_test_env_path)
else:
    load_dotenv()
```

#### Naming Conventions

- **Functions/variables**: `snake_case`
- **Internal functions**: `_leading_underscore`
- **Constants**: `UPPER_SNAKE_CASE`
- **MCP instance**: `mcp = FastMCP("ServiceName")`

### TypeScript (openclaw-map-mcp)

Follow openclaw TypeScript standards (see parent AGENTS.md):
- ESM modules
- Strict typing
- Oxlint/Oxfmt for formatting
- Node.js 22+

## Testing Guidelines

- Test files: `test_<service>.py`
- Import internal functions for testing: `from server import _get_weather_now`
- Use print-based output
- Include both unit tests and MCP protocol tests
- Always check environment variables before running

```python
def test_geocode():
    """测试地理编码功能"""
    print("\n" + "=" * 60)
    print("测试 1: 地理编码")
    # Test implementation
```

## Common Tasks

### Adding a New MCP Tool

1. Create private function `_tool_name()` with business logic
2. Create public decorated function `@mcp.tool() def tool_name()`
3. Add to test file
4. Update requirements.txt if needed

### API Host Configuration

QWeather requires dedicated API host from 2026:

```python
HEFENG_API_HOST = os.getenv("HEFENG_API_HOST")

if HEFENG_API_HOST:
    BASE_URL = f"https://{HEFENG_API_HOST}/v7"
else:
    BASE_URL = "https://devapi.qweather.com/v7"  # Deprecated
```

### Running a Single Service

```bash
# Map service
python Map/server.py

# Weather service
python Weather/server.py
```

## Project Structure

```
MCP/
├── Map/
│   ├── server.py          # Baidu Map MCP service (5 tools)
│   ├── test_map.py        # Unit tests
│   └── requirements.txt
├── Weather/
│   ├── server.py          # QWeather MCP service (6 tools)
│   ├── test_weather.py    # Unit tests
│   └── requirements.txt
└── openclaw-map-mcp/      # TypeScript extension
    ├── src/
    ├── package.json
    └── tsconfig.json
```

## Security Guidelines

- Never commit API keys
- Use `.env` files (loaded from parent directories as fallback)
- Return error messages as strings (not exceptions) for tool outputs
- Use `SecretStr` for sensitive values in agent code (not in MCP services)

## Important Notes

1. **FastMCP 2.x**: Tool decorators wrap functions as FunctionTool objects - always separate business logic
2. **Session Management**: MCP services run as stdio subprocesses; keep them stateless
3. **Error Handling**: Return descriptive error strings (Chinese) for user display
4. **Timeouts**: Always set HTTP timeouts (e.g., `timeout=10`)
5. **Windows Encoding**: Avoid emoji characters; use `[xxx]` format instead
