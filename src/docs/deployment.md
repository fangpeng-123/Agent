# 部署文档

## 环境要求

- Python 3.10+
- pip / conda

## 安装步骤

```bash
# 1. 克隆项目
git clone <repo_url>
cd ai_toy

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 添加 API_KEY
```

## 运行方式

### CLI 模式

```bash
python decoupled_agent.py
```

### API 服务

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Docker 部署（待完善）

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"]
```

## 监控

- 健康检查: `GET /api/v1/health/`
- 性能指标: 待集成
