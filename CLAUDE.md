# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Agent system based on a decoupled architecture with a three-stage pipeline: "Intent Routing → Tool Execution → Main Model Response". The system supports rapid tool extension and module reuse, currently featuring weather and map tools with a FastAPI web service.

## Common Development Commands

### Installation and Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env  # Then edit .env to add API keys
```

### Running the Application
```bash
# CLI mode
python decoupled_agent.py

# FastAPI web service
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Alternative with reload during development
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing
```bash
# Run all tests
pytest src/tests/

# Run specific test module
pytest src/tests/unit/test_intent.py

# Run tests with verbose output
pytest -v src/tests/

# Run integration tests only
pytest src/tests/integration/
```

### Testing API Endpoints
```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Chat endpoint
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "合肥今天天气怎么样？"}'
```

### Testing Individual Tool Modules
```bash
# Test weather tools
python Function_Call/Weather/example_usage.py

# Test map tools
python Function_Call/Map/example_usage.py

# Test agent demo
python Function_Call/agent_demo.py

# Verify imports
python -c "from Function_Call import ALL_TOOLS, ALL_FUNCTIONS; print('OK')"
```

## Architecture Overview

The system uses a **dual architecture** approach:

### New Architecture (Default)
1. **ReQuery Intent Recognition**: LLM-based query rewriting and parameter extraction
2. **Parallel Tool Agents**: Multiple tool agents evaluate relevance and execute in parallel
3. **Main Model Streaming Response**: Generates response with streaming and optional TTS

### Old Architecture (Legacy)
1. **Rule-based Intent Classification**: Keyword/regex-based classification (millisecond response)
2. **Tool Execution**: Direct tool invocation based on intent
3. **Main Model Response**: Generates response

### Key Modules

- `src/core/agent.py`: Main `DecoupledAgent` class with both architectures
- `src/core/intent.py`: Rule-based intent classification (old architecture)
- `src/core/requery.py`: LLM-based query rewriting (new architecture)
- `src/core/executor.py`: Tool execution engine (old architecture)
- `src/core/tool_agent_executor.py`: Parallel tool agent execution (new architecture)
- `src/core/builder.py`: Message construction for LLM calls
- `Function_Call/`: Reusable tool modules (Weather, Map, UserProfile, DateTime)
- `api/`: FastAPI web service layer

### Tool Architecture

Each tool follows the OpenAI Function Call format and consists of:
- `XX_TOOLS`: List of tool definitions in OpenAI format
- `XX_FUNCTIONS`: Dictionary mapping tool names to implementations
- Individual tool functions with type hints

Tools are imported via `from Function_Call import ALL_TOOLS, ALL_FUNCTIONS`.

## Configuration

Configuration is managed via `config.yaml`:
- API host/port settings
- Model provider and parameters (OpenAI-compatible)
- Cache settings (weather TTL)
- Tool timeouts
- RAG vector store paths
- Logging configuration

Environment variables (`.env` file):
- `HEFENG_KEY`: Weather API key (and风天气)
- `HEFENG_API_HOST`: Weather API host
- `BAIDU_MAP_AK`: Baidu Map API key

## Code Style Guidelines

- **Primary Language**: Chinese for comments, docstrings, and user-facing messages
- **Encoding**: UTF-8 (files should have `# -*- coding: utf-8 -*-` header)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `WEATHER_TOOLS`, `ALL_FUNCTIONS`)
- **Imports**: Standard library → Third-party → Local (separated by blank lines)
- **Type Hints**: Required for all function parameters and return values

### Tool Definition Format
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

## Performance Metrics

The system tracks detailed performance:
- Program start time
- Tools load duration
- Intent classification/requery duration
- Tool execution duration
- First token time (TTFT)
- Response generation time
- TTS synthesis time
- First audio playback time

Typical query time (Hefei weather query):
- Intent classification: ~0.03 ms (old) or ~300 ms (new ReQuery)
- Tool execution: ~800 ms
- Response generation: ~1300 ms
- **Total**: ~2-5 seconds

## Conversation Memory

The agent maintains conversation history with:
- Recent history carried in messages (last 15 messages)
- Full history stored in `self.conversation_history`
- Auto-truncation to 30 messages maximum
- Message structure: `{"role": "user|assistant", "content": "..."}`
