import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { McpMapClient } from "./mcp-client.js";
import { createMapTools } from "./tools.js";

export interface MapMcpConfig {
  mcpServerUrl?: string;
  mcpCommand?: string;
  mcpArgs?: string[];
  apiKey?: string;
  timeout?: number;
  defaultCity?: string;
  searchRadius?: number;
}

export default function register(api: OpenClawPluginApi) {
  const config = api.pluginConfig as MapMcpConfig | undefined;
  const logger = api.logger;

  logger.info("Initializing Map MCP plugin...");

  const mcpClient = new McpMapClient({
    serverUrl: config?.mcpServerUrl,
    command: config?.mcpCommand,
    args: config?.mcpArgs,
    apiKey: config?.apiKey || process.env.AMAP_API_KEY,
    timeout: config?.timeout || 30000,
  });

  let isConnected = false;

  api.on("gateway_start", async () => {
    try {
      logger.info("Connecting to MCP server...");
      await mcpClient.connect();
      isConnected = true;

      const availableTools = mcpClient.getAvailableTools();
      logger.info(`Connected to MCP server. Available tools: ${availableTools.map((t) => t.name).join(", ")}`);

      const mapTools = createMapTools(mcpClient);
      for (const tool of mapTools) {
        api.registerTool(tool);
      }
      logger.info(`Registered ${mapTools.length} map tools`);
    } catch (error: any) {
      logger.error(`Failed to connect to MCP server: ${error.message}`);
      isConnected = false;
    }
  });

  api.on("gateway_stop", async () => {
    if (isConnected) {
      logger.info("Disconnecting from MCP server...");
      await mcpClient.disconnect();
      isConnected = false;
    }
  });

  api.registerCommand({
    name: "map_status",
    description: "检查地图 MCP 服务连接状态",
    acceptsArgs: false,
    requireAuth: true,
    handler: async (ctx) => {
      if (!isConnected) {
        return {
          text: "❌ 地图 MCP 服务未连接",
        };
      }

      const tools = mcpClient.getAvailableTools();
      return {
        text: `✅ 地图 MCP 服务已连接\n\n可用工具 (${tools.length}):\n${tools.map((t) => `  • ${t.name}: ${t.description}`).join("\n")}`,
      };
    },
  });

  logger.info("Map MCP plugin registered");
}
