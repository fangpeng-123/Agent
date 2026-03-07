# AGENTS.md - AI Toy Project Guidelines

## Build, Test, and Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the decoupled agent demo
python decoupled_agent.py

# Run individual test files
python test_decoupled_tools.py
python test_message_format.py
python test_weather_diagnose.py
python test_e2e.py
python test_import.py

# Test imports
python -c "from Function_Call import ALL_TOOLS, ALL_FUNCTIONS; print(f'Loaded {len(ALL_TOOLS)} tools')"

# Lint with ruff
ruff check .
ruff check --fix .
```

## Code Style Guidelines

### Language and Comments
- **Python**: 3.10+ with type hints
- **Encoding**: UTF-8 (`# -*- coding: utf-8 -*-` header required)
- **Comments**: Chinese for comments, docstrings, and user-facing messages

### Imports
Order in three groups with blank lines:
```python
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Optional

from langchain_openai import ChatOpenAI

from Function_Call import ALL_TOOLS
from src.core.intent import IntentType
```

### Naming Conventions
- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Type Hints and Dataclasses
Always use type hints and dataclasses:
```python
@dataclass
class PerformanceMetrics:
    stage_times: Dict[str, float] = field(default_factory=dict)

async def classify(self, user_input: str) -> IntentResult:
    """分类用户意图"""
    pass
```

### Error Handling
Use try/except with specific exceptions and Chinese messages:
```python
try:
    result = json.loads(content.strip())
except Exception as e:
    print(f"[WARN] 意图解析失败: {e}")
    return default_value
```

### Async Patterns
Use `async`/`await` for I/O operations and `asyncio.run()` in `if __name__ == "__main__"`.

## Architecture

### Decoupled Design
1. Intent Classification → Small model/fast rules
2. Tool Execution → Direct code execution
3. Response Generation → Large model (streaming)

### Logging Format
- `[OK]` - Success
- `[ERROR]` - Error
- `[WARN]` - Warning
- `[INFO]` - Information
- `[Stage X]` - Processing stage

## Testing
- Test files: `test_<feature>.py`
- Print-based verification
- Run: `python test_message_format.py`

## Security
- Never commit API keys
- Use `.env` file
- Use `SecretStr` for API keys

## Environment Variables
```env
API_KEY="your_langchain_api_key"
DASHSCOPE_API_KEY="your_qwen_tts_api_key"
```

## Project Structure
```
ai_toy/
├── decoupled_agent.py          # Core agent
├── decoupled_agent_demo.py     # Extended demo
├── requirements.txt            # Dependencies
├── .env                        # API keys
├── test_*.py                  # Test files
├── src/
│   ├── core/                   # Agent core
│   ├── services/               # TTS, ASR
│   └── utils/                  # Utilities
└── Function_Call/              # Tool definitions
```

## Adding a New Tool
1. Define tool in `Function_Call/` directory
2. Import via `from Function_Call import ALL_TOOLS, ALL_FUNCTIONS`

## Notes
1. Tool calls executed by code, not model
2. Conversation history: max 20 messages
3. Supports streaming and non-streaming modes
4. Performance metrics track each pipeline stage
