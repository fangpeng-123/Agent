# 法律知识问答机器人

基于RAG（检索增强生成）技术的法律领域智能问答系统，通过飞书提供便捷接入。

## 技术栈

- **后端框架**: FastAPI + LangChain + LlamaIndex
- **向量数据库**: Milvus Lite / FAISS (本地备选)
- **Embedding模型**: 本地BGE模型 或 阿里云Embedding API
- **LLM**: 阿里云通义千问API
- **飞书集成**: 飞书机器人API

## 核心特性

### 智能硬件检测
系统自动检测运行环境，选择最优方案：
- **有GPU**: 使用本地Embedding模型 + 本地LLM（如Qwen）
- **无GPU**: 自动切换到阿里云API服务（Embedding + LLM）

### 架构设计
```
用户提问 → 硬件检测 → 选择服务
                      ├─ GPU可用 → 本地模型推理
                      └─ 无GPU → 阿里云API
```

## 数据范围

- 中华人民共和国宪法（2018修正）
- 中华人民共和国民法典
- 中华人民共和国刑法

## 硬件要求

### 本地模型模式（需要GPU）
- **CPU**: Intel i5+/AMD R5+ (6核以上)
- **内存**: 16GB+
- **GPU**: NVIDIA GTX 1650 (4GB显存) 或更高
- **存储**: 50GB SSD

### API模式（无需GPU）
- **CPU**: 任意现代CPU
- **内存**: 8GB+
- **存储**: 20GB SSD

## 软件环境

- **操作系统**: Ubuntu 22.04 LTS / Windows 10+
- **Python**: 3.10
- **依赖**: 详见 requirements.txt

## 快速开始

### 1. 克隆项目

```bash
git clone <repo_url>
cd legal_agent
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 .\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填写以下配置:
# - FEISHU_APP_ID: 飞书应用ID
# - FEISHU_APP_SECRET: 飞书应用密钥
# - FEISHU_VERIFY_TOKEN: 飞书验证Token
# - DASHSCOPE_API_KEY: 阿里云API Key
# - USE_LOCAL_MODEL: true/false (是否强制使用本地模型)
```

### 4. 准备法律文档

```bash
# 将法律文档放入 data/documents 目录
# 支持 PDF 格式
mkdir -p data/documents
# 放入宪法、民法典、刑法 PDF 文件
```

### 5. 构建索引

```bash
python scripts/build_index.py
```

### 6. 启动服务

```bash
python code/main.py
```

### 7. 配置飞书

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 创建自建应用，获取 App ID 和 App Secret
3. 开通机器人能力，配置消息事件订阅
4. 将Webhook URL配置为 `https://your-domain.com/feishu/webhook`

## 智能切换说明

### 检测逻辑
```python
# 伪代码
def select_service():
    if USE_LOCAL_MODEL == "true":
        return LocalService()
    elif has_gpu() and has_enough_vram():
        return LocalService()
    else:
        return APIService()
```

### 服务选择
| 场景 | Embedding | LLM |
|-----|-----------|-----|
| 有GPU + 4GB+显存 | 本地BGE | 本地Qwen |
| 无GPU / 显存不足 | 阿里云Embedding API | 通义千问API |

### API配置
```yaml
# 阿里云API配置
ali_api:
  embedding:
    model: text-embedding-v2
    endpoint: https://dashscope.aliyuncs.com/api/v1/services/aigc/text-embedding/generation
  llm:
    model: qwen-turbo
    endpoint: https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
```

## 项目结构

```
legal_agent/
├── code/                      # 代码目录
│   ├── main.py               # FastAPI主应用
│   ├── config.py             # 配置管理 + 硬件检测
│   ├── feishu/               # 飞书集成
│   │   ├── client.py         # 飞书API客户端
│   │   └── handler.py        # 消息处理
│   ├── rag/                  # RAG核心模块 (LangChain + LlamaIndex)
│   │   ├── document_loader.py    # 文档加载器
│   │   ├── text_splitter.py      # 文本分割器
│   │   ├── embedding.py          # Embedding服务
│   │   ├── indexer.py            # 向量索引
│   │   ├── retriever.py          # 检索器
│   │   └── pipeline.py           # RAG流程编排
│   ├── services/             # 服务层
│   │   ├── llm.py            # LLM服务(本地/阿里云)
│   │   ├── embedding.py      # Embedding服务(本地/阿里云)
│   │   ├── dialog.py         # 对话管理
│   │   └── safety.py         # 内容安全
│   └── models/               # 数据模型
│       └── schemas.py
├── data/
│   ├── documents/            # 法律文档(PDF)
│   └── sqlite/               # 对话历史
├── scripts/
│   └── build_index.py        # 索引构建脚本
├── config.yaml               # 配置文件
├── requirements.txt          # Python依赖
├── .env.example              # 环境变量模板
└── README.md                 # 项目说明
```

## API接口

| 接口 | 方法 | 说明 |
| :--- | :--- | :--- |
| `/` | GET | 根路径 |
| `/health` | GET | 健康检查 |
| `/feishu/webhook` | POST | 飞书回调 |
| `/api/v1/query` | POST | 问答接口 |
| `/api/v1/history` | GET | 对话历史 |
| `/api/v1/service/status` | GET | 服务状态(本地/API) |

## 配置说明

### config.yaml

```yaml
# 服务模式配置
service:
  mode: auto  # auto/local/api
  local_model_path: ./models

# Embedding配置
embedding:
  local:
    model_name: BAAI/bge-small-zh
    device: cuda  # cuda/cpu
  api:
    provider: ali
    model: text-embedding-v2

# LLM配置
llm:
  local:
    model_name: Qwen/Qwen2.5-7B-Instruct
    device: cuda
  api:
    provider: ali
    model: qwen-turbo

# RAG配置
rag:
  top_k: 5
  max_history: 5
  chunk_size: 500
  chunk_overlap: 100

# 服务器配置
server:
  host: 0.0.0.0
  port: 8000
```

## 硬件检测示例

```python
from code.config import HardwareDetector

detector = HardwareDetector()

status = detector.check()
# {
#   "has_gpu": True,
#   "gpu_name": "NVIDIA GeForce GTX 1650",
#   "vram_gb": 4.0,
#   "recommended_mode": "local"
# }

service = detector.select_service()
# 返回 LocalService 或 APIService 实例
```

## 依赖清单

```
# 核心框架
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0

# LangChain + LlamaIndex
langchain>=0.1.0
langchain-community>=0.0.20
llama-index>=0.9.0
llama-index-vector-stores-milvus>=0.1.0

# 向量数据库
pymilvus>=2.3.0
faiss-cpu>=1.7.0  # 备选

# 模型推理
sentence-transformers>=2.2.0
torch>=2.0.0
transformers>=4.30.0

# 阿里云API
httpx>=0.26.0

# 工具库
python-dotenv>=1.0.0
python-multipart>=0.0.6
pymupdf>=1.23.0
jieba>=0.42.1
ahocorasick>=1.5.3
```

## 开发计划

### Phase 1: 基础框架
- [ ] 项目初始化
- [ ] FastAPI框架搭建
- [ ] 硬件检测模块实现
- [ ] 配置管理更新

### Phase 2: LangChain + LlamaIndex集成
- [ ] LangChain文档加载器
- [ ] LlamaIndex索引构建
- [ ] Embedding服务（本地/阿里云）
- [ ] LLM服务（本地/阿里云）

### Phase 3: RAG流程
- [ ] RAG Pipeline编排
- [ ] 向量检索实现
- [ ] Prompt模板优化

### Phase 4: 飞书集成
- [ ] 飞书应用创建
- [ ] 消息回调处理
- [ ] 单聊/群聊机器人

### Phase 5: 功能完善
- [ ] 多轮对话管理
- [ ] 对话历史存储
- [ ] 敏感词过滤
- [ ] 免责声明

## 常见问题

### Q: 如何强制使用本地模型？

A: 设置环境变量 `USE_LOCAL_MODEL=true`，或修改 `config.yaml` 中 `service.mode: local`

### Q: 显存不足怎么办？

A: 系统自动检测，如显存<4GB会自动切换到API模式。或手动配置 `service.mode: api`

### Q: 如何切换Embedding模型？

A: 修改 `config.yaml` 中 `embedding.local.model_name`，支持：
- `BAAI/bge-small-zh` (轻量，CPU可用)
- `BAAI/bge-base-zh` (中等，需要GPU)
- `BAAI/bge-large-zh` (重型，需要8GB+显存)

### Q: 飞书连接失败?

A: 检查Webhook URL是否公网可访问，确认HTTPS证书有效

## 免责声明

本系统提供的答案仅供参考，不构成法律意见。
涉及具体法律问题请咨询专业律师。
