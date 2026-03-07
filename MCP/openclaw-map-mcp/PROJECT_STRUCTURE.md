# 项目结构

```
openclaw-map-mcp/
├── src/
│   ├── index.ts              # 插件入口，注册到 OpenClaw
│   ├── mcp-client.ts         # MCP 客户端封装
│   └── tools.ts             # OpenClaw 工具定义和映射
├── dist/                   # 编译输出（自动生成）
├── node_modules/            # 依赖（自动生成）
├── .env.example            # 环境变量示例
├── .gitignore             # Git 忽略规则
├── LICENSE                # MIT 许可证
├── openclaw.plugin.json   # OpenClaw 插件清单
├── package.json           # NPM 包配置
├── tsconfig.json         # TypeScript 配置
├── README.md            # 项目说明文档
├── QUICKSTART.md        # 快速开始指南
├── CONFIG_EXAMPLES.md   # 配置示例
└── DEPLOYMENT.md       # 部署指南
```

## 核心文件说明

### src/index.ts

插件主入口文件，负责：
- 初始化 MCP 客户端
- 注册 OpenClaw 工具
- 处理生命周期事件（gateway_start, gateway_stop）
- 注册自定义命令（/map_status）

### src/mcp-client.ts

MCP 客户端封装类，提供：
- 连接管理（SSE/stdio 传输）
- 工具发现和调用
- 高级方法封装（searchAddress, geocode, routePlanning 等）
- 错误处理和超时控制

### src/tools.ts

OpenClaw 工具定义，将 MCP 工具映射为 OpenClaw 工具：
- `map_search`: 地址搜索
- `map_geocode`: 地理编码
- `map_reverse_geocode`: 逆地理编码
- `map_route`: 路线规划
- `map_nearby`: 周边搜索

### openclaw.plugin.json

插件清单文件，定义：
- 插件 ID 和元数据
- 配置 Schema（JSON Schema）
- 插件描述

### package.json

NPM 包配置，包含：
- 依赖项（@modelcontextprotocol/sdk）
- 构建脚本
- 对等依赖（openclaw）

## 数据流

```
用户请求
    ↓
OpenClaw Agent
    ↓
map_* 工具调用
    ↓
OpenClaw Tool Handler
    ↓
MCP Client (mcp-client.ts)
    ↓
MCP Protocol (SSE/stdio)
    ↓
Map MCP Server (@amap/mcp-server)
    ↓
Map API (高德地图)
    ↓
返回结果
    ↓
用户响应
```

## 扩展开发

### 添加新的地图工具

1. 在 `src/tools.ts` 中添加工具定义：

```typescript
tools.push({
  name: "map_new_feature",
  description: "新功能描述",
  inputSchema: {
    type: "object",
    properties: {
      param1: {
        type: "string",
        description: "参数说明",
      },
    },
    required: ["param1"],
  },
  handler: async (params: any) => {
    const result = await mcpClient.callTool("mcp_tool_name", params);
    return { success: true, data: result };
  },
});
```

2. 在 `src/mcp-client.ts` 中添加便捷方法（可选）：

```typescript
async newFeature(param1: string): Promise<unknown> {
  return this.callTool("mcp_tool_name", { param1 });
}
```

### 支持其他地图服务

修改 `openclaw.plugin.json` 中的默认配置：

```json
{
  "configSchema": {
    "properties": {
      "mcpArgs": {
        "default": ["@baidu/mcp-server"],
        "examples": [
          ["@amap/mcp-server"],
          ["@baidu/mcp-server"],
          ["@tencent/mcp-server"]
        ]
      }
    }
  }
}
```

## 测试

### 单元测试

```bash
npm test
```

### 集成测试

```bash
# 启动测试 Gateway
openclaw gateway --port 18789 --test

# 发送测试消息
openclaw message send --to +1234567890 --message "测试地图搜索"
```

### 手动测试

1. 启动 Gateway
2. 连接任意聊天渠道
3. 发送测试命令：
   ```
   /map_status
   ```
4. 测试地图功能：
   ```
   查一下北京朝阳区的地址
   ```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 版本历史

### 1.0.0 (2025-02-05)

- 初始版本
- 支持 MCP stdio 和 SSE 传输
- 集成高德地图 MCP 服务器
- 提供 5 个核心地图工具
