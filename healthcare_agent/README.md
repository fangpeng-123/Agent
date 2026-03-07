# 健康管理助手

基于企业微信的 AI 健康管理助手，为用户提供体检报告解读、健康咨询、个性化健康建议服务。

## 项目概述

本项目是一个基于 FastAPI + LangChain + LlamaIndex 的健康管理服务，通过企业微信应用接入，为用户提供 7x24h 的健康咨询和体检报告解析服务。

### 核心功能

- 企微消息接入与处理
- 健康知识问答（基于 RAG）
- 体检报告解析与健康画像
- 分级审核机制（L0-L3）
- 用户管理与会员体系
- 对话历史管理

## 技术栈

- **开发语言**: Python 3.11+
- **Web 框架**: FastAPI
- **LLM 框架**: LangChain
- **RAG 框架**: LlamaIndex
- **向量数据库**: Chroma
- **LLM 提供商**: 通义千问（阿里云）
- **数据库**: SQLite
- **部署方式**: Docker Compose

## 项目结构

```
health_care/
├── code/                      # 源代码目录
│   ├── __init__.py
│   ├── main.py               # FastAPI 主入口
│   ├── config.py             # 配置管理
│   ├── models/              # 数据模型
│   │   └── schemas.py
│   ├── wechat/              # 企微消息处理
│   │   └── handler.py
│   ├── rag/                 # RAG 相关
│   │   ├── document_loader.py
│   │   ├── embedding.py
│   │   ├── indexer.py
│   │   └── pipeline.py
│   ├── report/              # 体检报告解析
│   │   └── parser.py
│   ├── services/            # 业务服务
│   │   ├── dialog.py
│   │   ├── safety.py
│   │   └── llm.py
│   ├── review/              # 客服审核
│   │   └── service.py
│   └── user/               # 用户管理
│       └── service.py
├── scripts/                # 脚本工具
│   └── build_index.py
├── data/                   # 数据目录
│   ├── index/              # 向量索引
│   ├── reports/            # 体检报告
│   └── sqlite/            # 数据库
├── logs/                  # 日志目录
├── config.yaml            # 配置文件
├── requirements.txt       # 依赖包
├── Dockerfile            # Docker 镜像
├── docker-compose.yml    # Docker Compose
└── .env.example         # 环境变量模板
```

## 快速开始

### 1. 环境准备

确保已安装以下软件：
- Python 3.11+
- Docker & Docker Compose（可选）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境变量模板并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下必要配置：

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
WECHAT_WORK_CORP_ID=your_corp_id
WECHAT_WORK_AGENT_ID=your_agent_id
WECHAT_WORK_SECRET=your_secret
```

### 4. 构建知识库索引

将健康知识文档放入 `data/knowledge/` 目录，然后运行：

```bash
python scripts/build_index.py
```

### 5. 启动服务

#### 方式一：直接运行

```bash
python -m code.main
```

#### 方式二：使用 Docker

```bash
docker-compose up -d
```

服务启动后，访问 http://localhost:8000 查看 API 文档。

## API 接口

### 健康检查

```
GET /health
```

### 查询接口

```
POST /api/v1/query
Content-Type: application/json

{
  "question": "如何保持健康的生活方式？",
  "user_id": "user123",
  "session_id": "session456"
}
```

### 企微回调

```
POST /wechat/webhook
```

### 对话历史

```
GET /api/v1/history/{user_id}
DELETE /api/v1/history/{session_id}
```

## 配置说明

### config.yaml

主要配置项：

- `service`: 服务模式配置
- `embedding`: Embedding 模型配置
- `llm`: LLM 模型配置
- `rag`: RAG 参数配置
- `wechat_work`: 企微应用配置
- `review`: 审核机制配置
- `report`: 体检报告解析配置

详细配置说明请参考 [健康助手PRD.md](./健康助手PRD.md)

## 分级审核机制

| 级别 | 问题类型 | 处理方式 |
|------|----------|----------|
| L0 | 基础健康知识、定义解释 | 直接回复 |
| L1 | 饮食建议、运动方案 | AI 回复 → 客服抽检 |
| L2 | 科室推荐、医院选择 | AI 回复 → 客服审核 |
| L3 | 诊断建议、用药指导 | AI 回复 → 客服确认 |

## 部署

### Docker 部署

```bash
docker-compose up -d
```

### 云服务器部署

1. 上传代码到服务器
2. 配置环境变量
3. 构建知识库索引
4. 启动服务

## 开发指南

### 添加新的知识文档

1. 将文档放入 `data/knowledge/` 目录
2. 运行 `python scripts/build_index.py` 重建索引

### 扩展企微功能

修改 `code/wechat/handler.py` 中的消息处理逻辑。

### 自定义审核规则

修改 `config.yaml` 中的 `review.levels` 配置。

## 注意事项

1. **企微应用资质**: 需要企业微信认证，需要企业营业执照
2. **域名要求**: 回调 URL 需要 ICP 备案和 HTTPS 证书
3. **API 密钥**: 请妥善保管 DASHSCOPE_API_KEY 等敏感信息

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题，请参考 [健康助手PRD.md](./健康助手PRD.md) 或联系项目维护者。
