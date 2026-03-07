# AGENTS.md - Coding Guidelines for Agentic Agents

This document provides guidelines for AI agents working in this repository.

## Repository Overview

This is a monorepo containing multiple projects:

- **openclaw/** - TypeScript WhatsApp gateway CLI with Pi RPC agent (main project)
- **health_care/** - Python health management assistant with RAG
- **legal_agent/** - Python legal assistant agent
- **MCP/** - Model Context Protocol servers (Weather, Map)
- **agent_test/** - Test utilities

## Build, Test, and Lint Commands

### TypeScript Projects (openclaw)

```bash
# Install dependencies
pnpm install

# Build
pnpm build

# Run all checks (typecheck + lint + format)
pnpm check

# Lint only
pnpm lint

# Fix lint issues
pnpm lint:fix

# Format check
pnpm format

# Format fix
pnpm format:fix

# Run all tests
pnpm test

# Run single test file
pnpm vitest run src/utils.test.ts

# Run tests in watch mode
pnpm test:watch

# Run tests with coverage
pnpm test:coverage

# Run e2e tests
pnpm test:e2e

# Run live tests (requires API keys)
pnpm test:live
```

### Python Projects

```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
python -m code.main

# Run individual test files
python test_weather.py
python test_map.py
```

## Code Style Guidelines

### TypeScript (openclaw)

- **Language**: TypeScript with ESM modules (`"type": "module"`)
- **Strict Mode**: Enabled - avoid `any` types
- **Imports**: Use `node:` prefix for Node.js built-ins (e.g., `import fs from "node:fs"`)
- **Formatting**: Oxfmt (enforced in CI)
- **Linting**: Oxlint with type-aware rules
- **Test Files**: Colocated as `*.test.ts` alongside source files
- **File Size**: Keep files under ~500-700 LOC; split when feasible

**Example:**
```typescript
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { myFunction } from "./utils.js";

export async function ensureDir(dir: string) {
  await fs.promises.mkdir(dir, { recursive: true });
}

describe("ensureDir", () => {
  it("creates nested directory", async () => {
    const result = await ensureDir("/tmp/test");
    expect(result).toBeUndefined();
  });
});
```

### Python (health_care, legal_agent, MCP)

- **Style**: PEP 8 compliant
- **Imports**: Standard library first, third-party second, local last
- **Types**: Use type hints with Pydantic models for data validation
- **Comments**: Use Chinese for comments and docstrings in healthcare/legal projects
- **Configuration**: YAML-based config files

**Example:**
```python
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

class ServiceConfig(BaseModel):
    mode: str = "auto"
    local_model_path: str = "./models"
```

## Naming Conventions

### TypeScript

- Functions/variables: `camelCase`
- Types/Interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE` for true constants
- Files: `kebab-case.ts` for multi-word files
- Test files: `*.test.ts` or `*.e2e.test.ts`

### Python

- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`
- Files: `snake_case.py`

## Error Handling

### TypeScript

- Use explicit error types where possible
- Avoid bare `throw` - always throw `Error` instances
- Use assertions for type narrowing (`asserts` keyword)

```typescript
export function assertWebChannel(input: string): asserts input is WebChannel {
  if (input !== "web") {
    throw new Error("Web channel must be 'web'");
  }
}
```

### Python

- Use try/except with specific exceptions
- Return typed responses for API endpoints
- Use Pydantic validation for input sanitization

```python
try:
    result = await some_async_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

## Testing Guidelines

### TypeScript (Vitest)

- Framework: Vitest with V8 coverage
- Coverage thresholds: 70% lines/functions/statements, 55% branches
- Test timeout: 120s (180s on Windows)
- Pool: forks (not threads)
- Max workers: 16 local, 3 in CI

```typescript
import { describe, expect, it, vi } from "vitest";
import { myFunction } from "./utils.js";

describe("myFunction", () => {
  it("should handle valid input", async () => {
    const result = await myFunction("test");
    expect(result).toBe("expected");
  });

  it("should throw on invalid input", () => {
    expect(() => myFunction("")).toThrow();
  });
});
```

### Python

- Simple test functions (not using pytest)
- Print-based output for manual verification
- Async test functions where needed

## Import Organization

### TypeScript

1. Node.js built-ins (with `node:` prefix)
2. Third-party packages
3. Local imports (with `.js` extension)

```typescript
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { myUtil } from "./utils.js";
import { config } from "../config/paths.js";
```

### Python

1. Standard library
2. Third-party packages
3. Local modules

```python
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from .config import load_config
```

## Git Workflow

- Use `scripts/committer "<msg>" <file...>` for commits
- Prefer rebase for clean history
- Use squash for messy history
- Always run `pnpm check && pnpm test` before pushing

## Security Guidelines

- Never commit real API keys, phone numbers, or credentials
- Use `.env.example` for environment variable templates
- Store credentials in `~/.openclaw/credentials/` (openclaw)
- Use `os.getenv()` for environment variables in Python

## Project-Specific Notes

### openclaw

- WhatsApp gateway with multiple channel support
- Extensions live in `extensions/*` as workspace packages
- Plugins use `openclaw/plugin-sdk` for runtime
- Docs hosted on Mintlify (docs.openclaw.ai)

### health_care / legal_agent

- FastAPI-based services
- RAG pipeline with ChromaDB
- WeChat Work integration
- Multi-level review system for healthcare responses

### MCP Servers

- Weather: QWeather API integration
- Map: Mapbox integration
- Use stdio transport for MCP protocol

## Common Tasks

### Running a Single Test

**TypeScript:**
```bash
pnpm vitest run src/utils.test.ts
pnpm vitest run src/utils.test.ts --reporter=verbose
```

**Python:**
```bash
python test_weather.py
```

### Adding a New Extension (openclaw)

1. Create directory in `extensions/my-extension/`
2. Add `package.json` with proper dependencies
3. Use `openclaw` in `devDependencies` or `peerDependencies` (not `dependencies`)
4. Add source files in `src/`
5. Add tests as `src/*.test.ts`

### Adding a New Python Service

1. Create module in `code/<module>/`
2. Add `__init__.py`
3. Use dataclasses or Pydantic for config
4. Update `config.yaml` with new section
5. Add to `code/main.py` routes

## Documentation

- TypeScript: Use JSDoc for public APIs
- Python: Use docstrings (Chinese for health/legal projects)
- Markdown: Follow existing formats
- Links: Use root-relative for internal docs, absolute for external

## Environment Setup

### Required

- Node.js 22+ (for openclaw)
- pnpm 10.23.0+ (for openclaw)
- Python 3.10+ (for Python projects)

### Optional

- Docker (for e2e tests)
- Swift/Xcode (for iOS/macOS apps)
- Android SDK (for Android app)
