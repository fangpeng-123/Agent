# AGENTS.md - Function_Call Project Guidelines

This document provides guidelines for AI agents working in the Function_Call repository.

## Project Overview

This project converts MCP (Model Context Protocol) tools to OpenAI Function Call format for LLM integration. It provides weather and map tools that can be directly used with OpenAI's function calling API or LangChain.

## Build, Test, and Development Commands

```bash
# Install dependencies
pip install httpx python-dotenv

# Run individual tool modules
python Weather/weather_tools.py
python Map/map_tools.py

# Run example usage scripts
python Weather/example_usage.py
python Map/example_usage.py
python agent_demo.py

# Test imports
python -c "from Function_Call import ALL_TOOLS, ALL_FUNCTIONS; print('OK')"

# Lint with ruff (if configured)
ruff check .
ruff check --fix .
```

## Code Style Guidelines

### Language and Comments

- **Primary Language**: Chinese for comments, docstrings, and user-facing messages
- **Code**: Python 3.10+ with type hints
- **Encoding**: UTF-8 (files should have `# -*- coding: utf-8 -*-` header)

### Imports

Order imports in three groups with blank lines between:

1. Standard library imports
2. Third-party package imports
3. Local module imports

```python
import os
from pathlib import Path
from typing import Dict, Any, List

import httpx
from dotenv import load_dotenv
```

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `WEATHER_TOOLS`, `BASE_URL`)
- **Private functions**: `_leading_underscore`
- **Tool definitions**: UPPER_SNAKE_CASE ending with `_TOOLS`
- **Function mappings**: UPPER_SNAKE_CASE ending with `_FUNCTIONS`

### Type Hints

Always use type hints for function parameters and return values:

```python
def get_weather_now(location: str) -> str:
    """获取指定城市的实时天气情况"""
    pass

WEATHER_TOOLS: List[Dict[str, Any]] = [...]
```

### Tool Definition Format

Follow OpenAI Function Call format:

```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "工具描述",
        "parameters": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
}
```

### Error Handling

Use try/except with specific exceptions and Chinese error messages:

```python
try:
    response = httpx.get(url, params=params, timeout=10)
    data = response.json()
except Exception as e:
    return f"请求异常：{str(e)}"
```

### Environment Variables

Load environment variables at module level:

```python
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

API_KEY = os.getenv("API_KEY")
```

### Docstrings

Use Chinese docstrings with triple quotes:

```python
def get_weather_now(location: str) -> str:
    """
    获取指定城市的实时天气情况

    Args:
        location: 城市名称或LocationID

    Returns:
        实时天气信息
    """
```

### Logging and Output

Use consistent log prefixes:

- `[OK]` - Success
- `[ERROR]` - Error
- `[INFO]` - Information

## Project Structure

```
Function_Call/
├── __init__.py              # Main package initialization
├── agent_demo.py            # Integration demo
├── README.md                # Documentation
├── Weather/                 # Weather tools
│   ├── __init__.py
│   ├── weather_tools.py     # Tool implementations
│   └── example_usage.py     # Usage examples
└── Map/                     # Map tools
    ├── __init__.py
    ├── map_tools.py         # Tool implementations
    └── example_usage.py     # Usage examples
```

## Common Tasks

### Adding a New Tool

1. Add tool definition to `XX_TOOLS` list
2. Implement the function with proper type hints
3. Add function to `XX_FUNCTIONS` dictionary
4. Export in `__init__.py`
5. Update README.md

### Testing Tools

```bash
# Test individual tool
python -c "from Weather.weather_tools import get_weather_now; print(get_weather_now('北京'))"

# Test full import
python -c "from Function_Call import ALL_TOOLS; print(len(ALL_TOOLS))"
```

## Security Guidelines

- Never commit real API keys
- Use `.env` file for credentials
- Load from parent directory as fallback:
  `Path(__file__).parent.parent.parent / "agent_test" / ".env"`

## Required Environment Variables

```env
HEFENG_KEY="your_qweather_key"
HEFENG_API_HOST="your.qweatherapi.com"
BAIDU_MAP_AK="your_baidu_map_key"
```
