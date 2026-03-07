import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import type { Tool } from "@modelcontextprotocol/sdk/types.js";

export interface McpClientConfig {
  serverUrl?: string;
  command?: string;
  args?: string[];
  apiKey?: string;
  timeout?: number;
}

export class McpMapClient {
  private client: Client | null = null;
  private transport: SSEClientTransport | StdioClientTransport | null = null;
  private tools: Map<string, Tool> = new Map();
  private config: McpClientConfig;

  constructor(config: McpClientConfig) {
    this.config = {
      timeout: 30000,
      command: "npx",
      args: ["@amap/mcp-server"],
      ...config,
    };
  }

  async connect(): Promise<void> {
    if (this.client) {
      await this.disconnect();
    }

    this.client = new Client(
      {
        name: "openclaw-map-mcp",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );

    if (this.config.serverUrl) {
      this.transport = new SSEClientTransport(
        new URL(this.config.serverUrl)
      );
    } else {
      this.transport = new StdioClientTransport({
        command: this.config.command!,
        args: this.config.args!,
        env: this.config.apiKey ? {
          AMAP_API_KEY: this.config.apiKey,
        } : undefined,
      });
    }

    await this.client.connect(this.transport);

    const toolsResult = await this.client.listTools();
    if (toolsResult.tools) {
      for (const tool of toolsResult.tools) {
        this.tools.set(tool.name, tool);
      }
    }
  }

  async disconnect(): Promise<void> {
    if (this.client) {
      await this.client.close();
      this.client = null;
    }
    if (this.transport) {
      this.transport = null;
    }
    this.tools.clear();
  }

  getAvailableTools(): Tool[] {
    return Array.from(this.tools.values());
  }

  getTool(name: string): Tool | undefined {
    return this.tools.get(name);
  }

  hasTool(name: string): boolean {
    return this.tools.has(name);
  }

  async callTool(name: string, args: Record<string, unknown> = {}): Promise<unknown> {
    if (!this.client) {
      throw new Error("MCP client not connected");
    }

    if (!this.hasTool(name)) {
      throw new Error(`Tool not found: ${name}`);
    }

    const result = await this.client.callTool({
      name,
      arguments: args,
    });

    if (result.content && result.content.length > 0) {
      const textContent = result.content.find((item: any) => item.type === "text");
      if (textContent && "text" in textContent) {
        try {
          return JSON.parse(textContent.text as string);
        } catch {
          return textContent.text;
        }
      }
    }

    return result;
  }

  async searchAddress(address: string, city?: string): Promise<unknown> {
    const toolName = this.findToolByFunction("search", "geocode", "address");
    if (!toolName) {
      throw new Error("No address search tool available");
    }

    return this.callTool(toolName, {
      address,
      city: city || this.config.apiKey,
    });
  }

  async geocode(address: string, city?: string): Promise<unknown> {
    const toolName = this.findToolByFunction("geocode", "encode");
    if (!toolName) {
      throw new Error("No geocoding tool available");
    }

    return this.callTool(toolName, {
      address,
      city,
    });
  }

  async reverseGeocode(longitude: number, latitude: number): Promise<unknown> {
    const toolName = this.findToolByFunction("reverse", "decode");
    if (!toolName) {
      throw new Error("No reverse geocoding tool available");
    }

    return this.callTool(toolName, {
      longitude,
      latitude,
    });
  }

  async planRoute(
    origin: string,
    destination: string,
    mode: "driving" | "walking" | "bicycling" | "transit" = "driving"
  ): Promise<unknown> {
    const toolName = this.findToolByFunction("route", "direction", "path");
    if (!toolName) {
      throw new Error("No route planning tool available");
    }

    return this.callTool(toolName, {
      origin,
      destination,
      mode,
    });
  }

  async searchNearby(
    location: string,
    keywords: string,
    radius?: number
  ): Promise<unknown> {
    const toolName = this.findToolByFunction("nearby", "poi", "search");
    if (!toolName) {
      throw new Error("No nearby search tool available");
    }

    return this.callTool(toolName, {
      location,
      keywords,
      radius: radius || 1000,
    });
  }

  private findToolByFunction(...keywords: string[]): string | undefined {
    for (const [name, tool] of this.tools.entries()) {
      const searchStr = `${name} ${tool.description || ""} ${JSON.stringify(tool.inputSchema || {})}`.toLowerCase();
      if (keywords.some((keyword) => searchStr.includes(keyword.toLowerCase()))) {
        return name;
      }
    }
    return undefined;
  }
}
