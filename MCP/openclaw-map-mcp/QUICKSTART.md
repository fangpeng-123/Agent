# 快速开始指南

## 前提条件

- Node.js >= 22.12.0
- OpenClaw 已安装并运行
- 高德地图 API Key

## 步骤一: 获取高德地图 API Key

1. 访问 https://lbs.amap.com/
2. 注册/登录账号
3. 进入控制台 -> 应用管理 -> 我的应用
4. 创建新应用，选择"Web服务"
5. 复制 API Key

## 步骤二: 安装插件

```bash
# 进入插件目录
cd f:\code\Agent\openclaw-map-mcp

# 安装依赖
npm install

# 构建插件
npm run build

# 安装到 OpenClaw
cd f:\code\Agent\openclaw
openclaw plugins install ../openclaw-map-mcp
```

## 步骤三: 配置插件

编辑 OpenClaw 配置文件（通常在 `~/.openclaw/config.json`）：

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "mcpCommand": "npx",
          "mcpArgs": ["@amap/mcp-server"],
          "apiKey": "你的高德API密钥",
          "timeout": 30000,
          "defaultCity": "北京",
          "searchRadius": 1000
        }
      }
    }
  }
}
```

或者使用环境变量：

```bash
export AMAP_API_KEY="你的高德API密钥"
```

## 步骤四: 重启 OpenClaw Gateway

```bash
# 停止当前 Gateway
openclaw gateway stop

# 启动 Gateway
openclaw gateway --port 18789
```

## 步骤五: 验证安装

在任意已连接的聊天渠道（Telegram/WhatsApp/Discord等）中发送：

```
/map_status
```

应该看到类似输出：

```
✅ 地图 MCP 服务已连接

可用工具 (5):
  • map_search: 搜索地址或地点。支持模糊搜索和精确地址查询。
  • map_geocode: 将地址转换为经纬度坐标（地理编码）。
  • map_reverse_geocode: 将经纬度坐标转换为地址（逆地理编码）。
  • map_route: 规划两点之间的路线。支持驾车、步行、骑行和公交路线。
  • map_nearby: 搜索指定位置周边的设施或兴趣点（POI）。
```

## 步骤六: 开始使用

现在你可以直接在对话中使用地图功能：

```
用户: 帮我查一下北京朝阳区的望京SOHO
助手: [自动调用 map_search] 找到以下结果...

用户: 从望京SOHO到中关村怎么走？
助手: [自动调用 map_route] 推荐路线如下...

用户: 望京附近有什么好吃的餐厅？
助手: [自动调用 map_nearby] 发现以下餐厅...
```

## 常见问题

### Q: 提示 "MCP client not connected"

**A**: 检查以下几点：
1. Gateway 是否已重启
2. `@amap/mcp-server` 是否能正常下载和运行
3. API Key 是否正确配置
4. 查看日志：`openclaw logs`

### Q: 工具调用超时

**A**: 增加 `timeout` 配置值：
```json
{
  "timeout": 60000
}
```

### Q: 搜索结果不准确

**A**: 在搜索时指定城市：
```
用户: 查一下上海的南京路
```

或者在配置中设置默认城市。

## 下一步

- 查看 [README.md](./README.md) 了解详细配置
- 查看 [openclaw.plugin.json](./openclaw.plugin.json) 了解所有配置选项
- 查看 [src/tools.ts](./src/tools.ts) 了解工具实现细节
