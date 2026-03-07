# 示例配置

## 最小配置

仅使用默认设置，通过环境变量设置 API Key：

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true
      }
    }
  }
}
```

环境变量：
```bash
export AMAP_API_KEY="your-api-key-here"
```

## 完整配置

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

## 使用 SSE 传输

如果 MCP 服务器以 SSE 模式运行：

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "mcpServerUrl": "http://localhost:8080/sse",
          "apiKey": "your-api-key",
          "timeout": 30000
        }
      }
    }
  }
}
```

## 使用本地 MCP 服务器

如果使用本地构建的 MCP 服务器：

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "mcpCommand": "node",
          "mcpArgs": ["/path/to/local/mcp-server/dist/index.js"],
          "apiKey": "your-api-key",
          "timeout": 30000
        }
      }
    }
  }
}
```

## 工具白名单配置

限制特定用户或群组只能使用部分地图工具：

```json
{
  "agents": {
    "defaults": {
      "tools": {
        "allow": ["map_search", "map_geocode"]
      }
    }
  }
}
```

## 多区域配置

为不同区域设置不同的默认城市：

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "apiKey": "your-api-key",
          "defaultCity": "北京"
        }
      }
    }
  },
  "channels": {
    "telegram": {
      "accounts": {
        "account1": {
          "agentId": "default",
          "agentConfig": {
            "tools": {
              "alsoAllow": ["map_nearby"]
            }
          }
        }
      }
    }
  }
}
```

## 调试配置

启用详细日志：

```json
{
  "logging": {
    "level": "debug",
    "plugins": true
  },
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "apiKey": "your-api-key",
          "timeout": 60000
        }
      }
    }
  }
}
```

## 生产环境配置

推荐的生产环境配置：

```json
{
  "plugins": {
    "entries": {
      "map-mcp": {
        "enabled": true,
        "config": {
          "mcpCommand": "npx",
          "mcpArgs": ["@amap/mcp-server"],
          "apiKey": "${AMAP_API_KEY}",
          "timeout": 30000,
          "defaultCity": "北京",
          "searchRadius": 2000
        }
      }
    }
  },
  "security": {
    "tools": {
      "elevated": ["map_route", "map_nearby"]
    }
  }
}
```

注意：`"${AMAP_API_KEY}"` 语法会从环境变量读取值。
