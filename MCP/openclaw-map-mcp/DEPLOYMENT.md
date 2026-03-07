# 部署指南

## 本地部署

### 开发环境

```bash
# 1. 克隆或创建插件目录
cd f:\code\Agent\openclaw-map-mcp

# 2. 安装依赖
npm install

# 3. 构建
npm run build

# 4. 链接到 OpenClaw（开发模式）
cd f:\code\Agent\openclaw
openclaw plugins install -l ../openclaw-map-mcp

# 5. 配置
# 编辑 ~/.openclaw/config.json

# 6. 启动 Gateway
openclaw gateway --port 18789
```

### 生产环境

```bash
# 1. 构建插件
cd f:\code\Agent\openclaw-map-mcp
npm install
npm run build

# 2. 安装到 OpenClaw
cd f:\code\Agent\openclaw
openclaw plugins install ../openclaw-map-mcp

# 3. 配置 API Key
export AMAP_API_KEY="your-production-api-key"

# 4. 重启 Gateway
openclaw gateway restart
```

## Docker 部署

### 方式一: 与 OpenClaw 一起部署

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  openclaw:
    image: ghcr.io/openclaw/openclaw:latest
    container_name: openclaw
    restart: unless-stopped
    ports:
      - "18789:18789"
    volumes:
      - ./openclaw-data:/root/.openclaw
      - ./openclaw-map-mcp:/plugins/map-mcp:ro
    environment:
      - AMAP_API_KEY=${AMAP_API_KEY}
      - NODE_ENV=production
```

启动：

```bash
docker-compose up -d
```

### 方式二: 独立部署 MCP 服务器

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mcp-server:
    image: node:22-alpine
    container_name: map-mcp-server
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - AMAP_API_KEY=${AMAP_API_KEY}
    command: >
      sh -c "
        npm install -g @amap/mcp-server &&
        npx @amap/mcp-server
      "

  openclaw:
    image: ghcr.io/openclaw/openclaw:latest
    container_name: openclaw
    restart: unless-stopped
    ports:
      - "18789:18789"
    volumes:
      - ./openclaw-data:/root/.openclaw
      - ./openclaw-map-mcp:/plugins/map-mcp:ro
    environment:
      - NODE_ENV=production
    depends_on:
      - mcp-server
```

配置 OpenClaw 使用 SSE 传输：

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "mcpServerUrl": "http://mcp-server:8080/sse",
          "timeout": 30000
        }
      }
    }
  }
}
```

## 服务器部署（VPS）

### 使用 systemd 管理

创建 `/etc/systemd/system/openclaw.service`:

```ini
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=openclaw
WorkingDirectory=/home/openclaw
Environment="AMAP_API_KEY=your-api-key"
ExecStart=/usr/local/bin/openclaw gateway --port 18789
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable openclaw
sudo systemctl start openclaw
sudo systemctl status openclaw
```

### 使用 PM2 管理

```bash
# 安装 PM2
npm install -g pm2

# 启动 OpenClaw
pm2 start openclaw --name openclaw -- gateway --port 18789

# 设置开机自启
pm2 startup
pm2 save

# 查看日志
pm2 logs openclaw
```

## 云平台部署

### Fly.io

创建 `fly.toml`:

```toml
app = "openclaw-map"

[build]
  builder = "dockerfile"

[env]
  AMAP_API_KEY = "your-api-key"

[[services]]
  http_checks = []
  internal_port = 18789

[vm]
  cpu = "1"
  memory = "512mb"
```

部署：

```bash
fly launch
fly deploy
```

### Railway

创建 `railway.toml`:

```toml
[build]
  builder = "NIXPACKS"

[deploy]
  healthcheckPath = "/health"
  healthcheckTimeout = 300
  restartPolicyType = "ON_FAILURE"
  restartPolicyMaxRetries = 10
```

部署：

```bash
railway up
```

## 监控和日志

### 查看插件日志

```bash
# OpenClaw 日志
openclaw logs

# 过滤地图插件日志
openclaw logs | grep map-mcp

# 实时查看
openclaw logs --follow
```

### 健康检查

```bash
# 检查 Gateway 状态
curl http://localhost:18789/health

# 检查插件状态
openclaw plugins list
```

### 性能监控

在配置中启用工具调用统计：

```json
{
  "agents": {
    "defaults": {
      "usage": {
        "enabled": true
      }
    }
  }
}
```

## 故障恢复

### 自动重启

配置 systemd 或 PM2 自动重启服务（见上文）。

### 备份配置

定期备份 OpenClaw 配置：

```bash
# 备份配置
cp ~/.openclaw/config.json ~/.openclaw/config.backup.$(date +%Y%m%d)

# 备份会话数据
tar -czf openclaw-backup-$(date +%Y%m%d).tar.gz ~/.openclaw/
```

### 回滚

如果更新后出现问题：

```bash
# 回滚到之前的版本
openclaw plugins update map-mcp --version 1.0.0

# 或重新安装
openclaw plugins disable map-mcp
openclaw plugins enable map-mcp
```

## 安全建议

1. **API Key 保护**: 使用环境变量或密钥管理服务
2. **网络隔离**: 在生产环境中使用内网或 VPN
3. **访问控制**: 配置工具白名单和用户权限
4. **日志审计**: 定期检查访问日志
5. **更新维护**: 及时更新插件和依赖

## 性能优化

1. **缓存**: 启用 OpenClaw 的内存缓存
2. **连接池**: MCP 客户端自动管理连接
3. **超时设置**: 根据网络情况调整 timeout
4. **并发控制**: 限制同时进行的地图请求

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "timeout": 30000
        }
      }
    }
  },
  "agents": {
    "defaults": {
      "concurrency": {
        "max": 3
      }
    }
  }
}
```
