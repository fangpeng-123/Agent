# AI Agent - 解耦智能体架构

## 项目简介

基于解耦架构设计的智能助手系统，采用"意图路由 → 工具执行 → 主模型回复"的三阶段流水线，支持快速扩展和模块复用。

## 核心特性

- **解耦设计**：意图分类、工具执行、回复生成独立模块
- **规则分类**：毫秒级意图识别，无需 API 调用
- **工具扩展**：支持天气、地图等工具，可快速扩展
- **性能监控**：完整的链路计时和性能报告
- **API 服务**：FastAPI 接口支持 Web 部署

## 已开发功能 ✅

| 模块 | 功能 | 状态 | 说明 |
|------|------|------|------|
| 意图分类 | 基于规则的意图识别 | ✅ 完成 | 毫秒级响应 |
| 工具执行 | 异步工具调用执行器 | ✅ 完成 | 支持同步/异步 |
| 天气工具 | 当前天气、预报、空气质量、生活指数 | ✅ 完成 | 和风天气 API |
| 地图工具 | 城市搜索、地理编码、周边搜索、导航 | ✅ 完成 | 百度地图 API |
| 性能监控 | 链路计时、性能报告 | ✅ 完成 | 完整阶段计时 |
| CLI 入口 | 命令行使用示例 | ✅ 完成 | 可直接运行 |
| FastAPI 服务 | Web API 接口 | ✅ 完成 | 聊天、天气、工具接口 |
| 健康检查 | 服务状态监控 | ✅ 完成 | /health 接口 |
| 对话历史 | 历史记录管理 | ✅ 完成 | 短期/长期记忆 |

## 待开发功能 🚧

| 模块 | 功能 | 优先级 | 说明 |
|------|------|--------|------|
| ASR | 语音识别服务接入 | 中 | 集成 ASR 引擎 |
| TTS | 语音合成服务接入 | 中 | 集成 TTS 引擎 |
| RAG | 用户画像向量检索 | 中 | ChromaDB 集成 |
| Web 搜索 | 公网搜索模块 | 中 | 搜索引擎封装 |
| 内容安全 | 敏感词过滤 | 中 | 敏感词库管理 |
| 缓存层 | 智能缓存策略 | 低 | 意图/结果缓存 |
| 认证 | API 认证中间件 | 低 | JWT 认证 |
| 限流 | 请求速率限制 | 低 | 防止 API 滥用 |
| 监控 | 性能指标收集 | 低 | Prometheus 集成 |
| 故事生成 | StoryGenerator 工具 | 低 | 儿童陪伴场景 |
| 知识库 | KnowledgeBase 工具 | 低 | RAG 检索增强 |
| 用户画像 | UserProfile 工具 | 低 | 个性化服务 |

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 添加 API_KEY 等
```

### CLI 模式运行

```bash
python decoupled_agent.py
```

### API 服务运行

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 测试接口

```bash
# 健康检查
curl http://localhost:8000/api/v1/health/

# 聊天接口
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "合肥今天天气怎么样？"}'
```

## 项目结构

```
ai_toy/
│
│ # ========== 根目录文件 ==========
│
│ ├── README.md                    # 项目说明文档
│ ├── AGENTS.md                   # AI Agent 开发规范
│ ├── requirements.txt             # Python 依赖列表
│ ├── config.yaml                  # 配置文件
│ └── decoupled_agent.py           # CLI 主入口
│
│ # ========== Function_Call（工具模块） ==========
│
│ └── Function_Call/               # 可复用工具目录
│     ├── __init__.py
│     ├── README.md
│     ├── Weather/                 # 天气工具 ✅
│     │   ├── __init__.py
│     │   └── weather_tools.py
│     ├── Map/                    # 地图工具 ✅
│     │   ├── __init__.py
│     │   └── map_tools.py
│     ├── StoryGenerator/         # 🚧 故事生成工具
│     │   └── __init__.py
│     ├── KnowledgeBase/          # 🚧 知识库工具
│     │   └── __init__.py
│     └── UserProfile/           # 🚧 用户画像工具
│         └── __init__.py
│
│ # ========== src（核心模块） ==========
│
│ └── src/                        # 核心智能体模块
│     ├── __init__.py             # 模块统一导出
│     │
│     ├── core/                   # 核心逻辑层
│     │   ├── __init__.py
│     │   ├── agent.py            # DecoupledAgent 主逻辑
│     │   ├── intent.py           # 意图分类
│     │   ├── executor.py         # 工具执行器
│     │   └── builder.py          # 消息构建器
│     │
│     ├── utils/                 # 通用工具层
│     │   ├── __init__.py
│     │   ├── config.py           # 配置和常量
│     │   ├── logger.py          # 结构化日志
│     │   ├── exceptions.py      # 异常定义
│     │   └── performance.py      # 性能监控
│     │
│     ├── services/              # 外部服务层
│     │   ├── __init__.py
│     │   ├── asr.py             # 🚧 语音识别
│     │   └── tts.py             # 🚧 语音合成
│     │
│     ├── prompts/               # Prompt 管理
│     │   ├── __init__.py
│     │   ├── prompt_versioning.py # 🚧 版本管理
│     │   ├── system_prompts/    # System Prompt
│     │   │   ├── __init__.py
│     │   │   ├── base.py
│     │   │   ├── child_companion.py
│     │   │   └── few_shots.py
│     │   └── intent_prompts/    # Intent Prompt
│     │       ├── __init__.py
│     │       ├── classifier.py
│     │       └── query_rewriter.py
│     │
│     ├── security/              # 内容安全
│     │   ├── __init__.py
│     │   ├── content_filter.py
│     │   ├── safety_checker.py
│     │   └── keywords/
│     │       ├── __init__.py
│     │       ├── violence.txt
│     │       ├── fear.txt
│     │       ├── adult.txt
│     │       └── sensitive_words.py
│     │
│     ├── memory/               # 对话记忆
│     │   ├── __init__.py
│     │   ├── chat_history.py
│     │   ├── short_term_memory.py
│     │   ├── long_term_memory.py
│     │   └── conversation_manager.py
│     │
│     ├── web_search/           # Web 搜索
│     │   ├── __init__.py
│     │   ├── search_engine.py
│     │   └── content_summarizer.py
│     │
│     ├── cache/               # 缓存层
│     │   ├── __init__.py
│     │   ├── intent_cache.py
│     │   ├── rag_cache.py
│     │   ├── response_cache.py
│     │   └── cache_manager.py
│     │
│     ├── data/                 # 数据存储
│     │   ├── __init__.py
│     │   ├── conversations/
│     │   ├── user_profiles/
│     │   └── analytics/
│     │
│     ├── RAG/                  # 向量检索
│     │   ├── __init__.py
│     │   ├── vector_store.py
│     │   ├── embeddings.py
│     │   └── user_profile.py
│     │
│     ├── tests/                # 测试文件
│     │   ├── __init__.py
│     │   ├── unit/
│     │   │   ├── test_intent.py
│     │   │   ├── test_message_builder.py
│     │   │   └── test_tools.py
│     │   ├── integration/
│     │   │   ├── test_conversation_flow.py
│     │   │   └── test_full_pipeline.py
│     │   └── conftest.py
│     │
│     ├── monitoring/           # 监控模块
│     │   ├── __init__.py
│     │   ├── metrics.py
│     │   ├── tracer.py
│     │   └── alerts.py
│     │
│     └── docs/                 # 技术文档
│         ├── api/
│         │   └── openapi.yaml
│         ├── architecture.md
│         ├── message_flow.md
│         └── deployment.md
│
│ # ========== api（FastAPI 服务） ==========
│
│ └── api/                       # FastAPI Web 服务
│     ├── main.py                # 应用入口
│     ├── models.py              # Pydantic 模型
│     ├── middleware.py          # 中间件
│     │
│     └── routes/                # API 路由
│         ├── __init__.py
│         ├── chat.py           # 聊天接口
│         ├── weather.py         # 天气接口
│         ├── tools.py          # 工具接口
│         ├── health.py         # 健康检查
│         ├── conversation.py   # 对话历史
│         └── user_profile.py   # 用户画像
│
│ # ========== model（本地模型） ==========
│
│ └── model/                     # 本地模型存放
```

## 架构分层

```
┌─────────────────────────────────────┐
│           api/ (FastAPI)            │  ← Web 层
├─────────────────────────────────────┤
│            src/                     │
│  ┌─────────────────────────────────┐│
│  │          core/                   ││  ← 核心逻辑层
│  │  agent │ intent │ executor │    ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │          utils/                  ││  ← 通用工具层
│  │ config │ logger │ exceptions │  ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │         services/                ││  ← 外部服务层
│  │    asr (🚧)    │    tts (🚧)    ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │    memory │ cache │ RAG │ ...   ││  ← 功能扩展层
│  └─────────────────────────────────┘│
├─────────────────────────────────────┤
│         Function_Call/              │  ← 工具层
│    Weather │ Map │ ... (可复用)      │
├─────────────────────────────────────┤
│              model/                 │  ← 模型层
└─────────────────────────────────────┘
```

## 导入方式

```python
# 核心模块（推荐）
from src import DecoupledAgent, IntentType, PerformanceMetrics
from src.core import rule_based_intent_classify, MessageBuilder

# 工具模块
from Function_Call import ALL_TOOLS, ALL_FUNCTIONS
```

## 配置说明

编辑 `config.yaml` 可调整：

```yaml
api:
  host: "0.0.0.0"
  port: 8000

model:
  provider: "openai"
  model_name: "qwen3-235b-a22b"
  temperature: 0.7
  streaming: true

cache:
  weather_ttl: 300  # 天气缓存 5 分钟
```

## 性能指标

典型查询耗时（合肥天气）：

| 阶段 | 耗时 |
|------|------|
| 意图分类 | ~0.03 ms |
| 工具执行 | ~800 ms |
| 回复生成 | ~1300 ms |
| **总耗时** | **~2-5 秒** |

## 技术栈

- **LLM**: OpenAI / 通义千问
- **框架**: LangChain
- **Web**: FastAPI
- **工具调用**: 和风天气 API、百度地图 API

## License

MIT
