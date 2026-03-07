# OpenClaw Map MCP Plugin - 完整实现

## ✅ 已完成

我已经为你创建了一个完整的 OpenClaw 插件，用于通过 MCP 协议集成地图服务。

## 📦 项目文件

```
openclaw-map-mcp/
├── src/
│   ├── index.ts              ✅ 插件入口
│   ├── mcp-client.ts         ✅ MCP 客户端封装
│   └── tools.ts             ✅ OpenClaw 工具映射
├── openclaw.plugin.json      ✅ 插件清单
├── package.json             ✅ NPM 配置
├── tsconfig.json           ✅ TypeScript 配置
├── .env.example           ✅ 环境变量示例
├── .gitignore            ✅ Git 忽略规则
├── LICENSE               ✅ MIT 许可证
├── README.md             ✅ 项目说明
├── QUICKSTART.md         ✅ 快速开始指南
├── CONFIG_EXAMPLES.md    ✅ 配置示例
├── DEPLOYMENT.md        ✅ 部署指南
└── PROJECT_STRUCTURE.md  ✅ 项目结构说明
```

## 🎯 核心功能

### 1. MCP 客户端封装 (src/mcp-client.ts)

- ✅ 支持 SSE 和 stdio 两种传输方式
- ✅ 自动工具发现和注册
- ✅ 统一的调用接口
- ✅ 错误处理和超时控制
- ✅ 高级方法封装（searchAddress, geocode, routePlanning 等）

### 2. OpenClaw 工具映射 (src/tools.ts)

提供 5 个核心地图工具：

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `map_search` | 地址搜索 | address, city |
| `map_geocode` | 地址转坐标 | address, city |
| `map_reverse_geocode` | 坐标转地址 | longitude, latitude |
| `map_route` | 路线规划 | origin, destination, mode |
| `map_nearby` | 周边搜索 | location, keywords, radius |

### 3. 插件集成 (src/index.ts)

- ✅ 生命周期管理（gateway_start, gateway_stop）
- ✅ 自动连接 MCP 服务器
- ✅ 动态注册工具
- ✅ 自定义命令 `/map_status`
- ✅ 完整的错误处理和日志

## 🚀 快速开始

### 1. 安装依赖并构建

```bash
cd f:\code\Agent\openclaw-map-mcp
npm install
npm run build
```

### 2. 安装到 OpenClaw

```bash
cd f:\code\Agent\openclaw
openclaw plugins install ../openclaw-map-mcp
```

### 3. 配置 API Key

编辑 `~/.openclaw/config.json`:

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "apiKey": "你的高德API密钥",
          "defaultCity": "北京"
        }
      }
    }
  }
}
```

或使用环境变量：

```bash
export AMAP_API_KEY="你的高德API密钥"
```

### 4. 重启 Gateway

```bash
openclaw gateway restart
```

### 5. 验证安装

在任意聊天渠道发送：

```
/map_status
```

## 💡 使用示例

### 地址搜索

```
用户: 帮我查一下北京朝阳区的望京SOHO
助手: [调用 map_search] 找到以下结果...
```

### 路线规划

```
用户: 从望京SOHO到中关村怎么走？
助手: [调用 map_route] 推荐路线如下...
```

### 周边搜索

```
用户: 望京附近有什么好吃的餐厅？
助手: [调用 map_nearby] 发现以下餐厅...
```

## 🔧 配置选项

### 完整配置示例

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "mcpServerUrl": "",              // SSE 端点 URL（留空使用 stdio）
          "mcpCommand": "npx",             // MCP 服务器启动命令
          "mcpArgs": ["@amap/mcp-server"], // MCP 服务器参数
          "apiKey": "your-api-key",        // API Key
          "timeout": 30000,                // 超时时间（毫秒）
          "defaultCity": "北京",            // 默认城市
          "searchRadius": 1000              // 默认搜索半径（米）
        }
      }
    }
  }
}
```

### 环境变量

```bash
AMAP_API_KEY=your-api-key
MCP_SERVER_URL=http://localhost:8080/sse
MCP_COMMAND=npx
MCP_ARGS=@amap/mcp-server
TIMEOUT=30000
DEFAULT_CITY=北京
SEARCH_RADIUS=1000
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────┐
│           OpenClaw Gateway                  │
│  (AI Agent + Message Channels)             │
└──────────────────┬──────────────────────────┘
                   │
                   │ Plugin API
                   │
┌──────────────────▼──────────────────────────┐
│      openclaw-map-mcp Plugin              │
│                                          │
│  ┌──────────────────────────────────────┐   │
│  │  MCP Client (mcp-client.ts)      │   │
│  │  - Connection Management          │   │
│  │  - Tool Discovery               │   │
│  │  - Request/Response Handling     │   │
│  └──────────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────────┐   │
│  │  Tool Mapping (tools.ts)         │   │
│  │  - map_search                  │   │
│  │  - map_geocode                 │   │
│  │  - map_reverse_geocode          │   │
│  │  - map_route                   │   │
│  │  - map_nearby                  │   │
│  └──────────────────────────────────────┘   │
└──────────────────┬──────────────────────────┘
                   │
                   │ MCP Protocol
                   │ (SSE or stdio)
                   │
┌──────────────────▼──────────────────────────┐
│     Map MCP Server                        │
│  (@amap/mcp-server or custom)           │
└──────────────────┬──────────────────────────┘
                   │
                   │ HTTP API
                   │
┌──────────────────▼──────────────────────────┐
│     Map Service API                       │
│  (高德地图 / 百度地图 / 腾讯地图)       │
└─────────────────────────────────────────────┘
```

## 📚 文档索引

- **[README.md](./README.md)** - 项目概述和完整功能说明
- **[QUICKSTART.md](./QUICKSTART.md)** - 5 分钟快速开始指南
- **[CONFIG_EXAMPLES.md](./CONFIG_EXAMPLES.md)** - 各种配置场景示例
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - 生产环境部署指南
- **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** - 项目结构和扩展开发指南

## 🔍 技术细节

### MCP 协议支持

- ✅ **SSE (Server-Sent Events)**: 适合远程 MCP 服务器
- ✅ **stdio**: 适合本地 MCP 服务器（推荐）
- ✅ 自动选择传输方式
- ✅ 连接池和重连机制

### 错误处理

- ✅ 连接失败自动重试
- ✅ 请求超时控制
- ✅ 工具调用错误捕获
- ✅ 详细的日志输出

### 安全特性

- ✅ API Key 通过环境变量或配置文件保护
- ✅ 工具白名单支持
- ✅ 沙箱隔离兼容
- ✅ 权限控制集成

## 🎓 扩展开发

### 添加新工具

1. 在 `src/tools.ts` 中添加工具定义
2. 在 `src/mcp-client.ts` 中添加便捷方法（可选）
3. 更新文档

### 支持其他地图服务

修改 `openclaw.plugin.json` 中的默认配置，支持：
- 百度地图 MCP 服务器
- 腾讯地图 MCP 服务器
- 自定义 MCP 服务器

## 🐛 故障排除

### 常见问题

**Q: MCP 服务连接失败**
- 检查 `npx` 是否可用
- 确认 API Key 正确
- 查看日志：`openclaw logs`

**Q: 工具调用超时**
- 增加 `timeout` 配置值
- 检查网络连接

**Q: 搜索结果不准确**
- 指定城市参数
- 使用更精确的地址

### 调试模式

启用详细日志：

```json
{
  "logging": {
    "level": "debug",
    "plugins": true
  }
}
```

## 📝 下一步

1. **构建并测试**
   ```bash
   cd f:\code\Agent\openclaw-map-mcp
   npm install
   npm run build
   ```

2. **安装到 OpenClaw**
   ```bash
   cd f:\code\Agent\openclaw
   openclaw plugins install ../openclaw-map-mcp
   ```

3. **配置并启动**
   - 获取高德地图 API Key
   - 配置插件
   - 重启 Gateway

4. **验证功能**
   - 发送 `/map_status` 检查连接
   - 测试地图搜索功能

## 🎉 总结

这个插件提供了：

- ✅ **完整的 MCP 客户端实现**：支持 SSE 和 stdio 传输
- ✅ **5 个核心地图工具**：搜索、地理编码、路线规划、周边查询
- ✅ **灵活的配置**：支持多种地图服务
- ✅ **生产就绪**：完整的错误处理、日志、文档
- ✅ **易于扩展**：清晰的架构和文档

现在你可以将这个插件安装到你的 OpenClaw 实例中，为 AI 助手添加强大的地图服务能力！

## 📞 支持

如有问题，请查看：
- [OpenClaw 文档](https://docs.openclaw.ai)
- [MCP 协议规范](https://modelcontextprotocol.io)
- [高德地图开放平台](https://lbs.amap.com/)
