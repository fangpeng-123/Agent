# OpenClaw Map MCP Plugin

为 OpenClaw 添加地图服务能力的插件，通过 MCP (Model Context Protocol) 协议集成高德地图等地图服务。

## 功能特性

- 📍 **地址搜索**: 支持模糊搜索和精确地址查询
- 🗺️ **地理编码**: 地址与经纬度坐标相互转换
- 🚗 **路线规划**: 支持驾车、步行、骑行、公交路线
- 🔍 **周边搜索**: 搜索指定位置周边的 POI（餐厅、加油站、医院等）

## 安装

### 方式一: 从本地安装

```bash
cd openclaw-map-mcp
npm install
npm run build

cd /path/to/openclaw
openclaw plugins install ../openclaw-map-mcp
```

### 方式二: 从 npm 安装（发布后）

```bash
openclaw plugins install openclaw-map-mcp
```

## 配置

在 OpenClaw 配置文件中添加插件配置：

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "mcpServerUrl": "",
          "mcpCommand": "npx",
          "mcpArgs": ["@amap/mcp-server"],
          "apiKey": "your-amap-api-key",
          "timeout": 30000,
          "defaultCity": "北京",
          "searchRadius": 1000
        }
      }
    }
  }
}
```

### 配置说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `mcpServerUrl` | string | 空 | MCP 服务器 SSE 端点 URL，留空则使用 stdio 传输 |
| `mcpCommand` | string | `npx` | 启动 MCP 服务器的命令 |
| `mcpArgs` | array | `["@amap/mcp-server"]` | MCP 服务器命令参数 |
| `apiKey` | string | - | 地图服务 API Key（也可通过 `AMAP_API_KEY` 环境变量设置） |
| `timeout` | number | `30000` | 请求超时时间（毫秒） |
| `defaultCity` | string | - | 默认搜索城市 |
| `searchRadius` | number | `1000` | 默认周边搜索半径（米） |

## 获取 API Key

1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 注册/登录账号
3. 创建应用并获取 Web 服务 API Key

## 使用

### 在对话中使用

安装并启用插件后，AI 助手会自动使用地图工具：

```
用户: 帮我查一下北京朝阳区的地址
助手: [调用 map_search 工具] 找到以下结果...

用户: 规划从望京到中关村的路线
助手: [调用 map_route 工具] 推荐路线如下...

用户: 附近有什么餐厅？
助手: [调用 map_nearby 工具] 发现以下餐厅...
```

### 检查服务状态

使用 `/map_status` 命令检查 MCP 服务连接状态：

```
/map_status
```

## 可用工具

| 工具名 | 描述 |
|--------|------|
| `map_search` | 搜索地址或地点 |
| `map_geocode` | 地址转经纬度 |
| `map_reverse_geocode` | 经纬度转地址 |
| `map_route` | 路线规划 |
| `map_nearby` | 周边设施搜索 |

## 开发

```bash
# 安装依赖
npm install

# 构建
npm run build

# 开发模式（监听文件变化）
npm run dev
```

## 架构说明

```
┌─────────────┐
│  OpenClaw   │
│  Gateway    │
└──────┬──────┘
       │
       │ Plugin API
       │
┌──────▼──────────────────────┐
│  openclaw-map-mcp Plugin  │
│  - MCP Client             │
│  - Tool Mapping           │
└──────┬────────────────────┘
       │
       │ MCP Protocol (SSE/stdio)
       │
┌──────▼──────────────────────┐
│  Map MCP Server           │
│  (e.g., @amap/mcp-server)│
└──────┬────────────────────┘
       │
       │ HTTP API
       │
┌──────▼──────────────────────┐
│  Map Service API          │
│  (高德地图/百度地图等)      │
└───────────────────────────┘
```

## 故障排除

### MCP 服务连接失败

1. 检查 `mcpCommand` 和 `mcpArgs` 配置是否正确
2. 确保 `npx` 可以正常执行
3. 检查 API Key 是否有效
4. 查看日志中的错误信息

### 工具调用失败

1. 使用 `/map_status` 检查服务状态
2. 确认参数格式是否正确
3. 检查网络连接

## 许可证

MIT

## 相关链接

- [OpenClaw 文档](https://docs.openclaw.ai)
- [MCP 协议规范](https://modelcontextprotocol.io)
- [高德地图开放平台](https://lbs.amap.com/)
