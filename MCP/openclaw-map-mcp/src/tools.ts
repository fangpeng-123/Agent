import type { AnyAgentTool } from "openclaw/plugin-sdk";
import type { McpMapClient } from "./mcp-client.js";

export function createMapTools(mcpClient: McpMapClient): AnyAgentTool[] {
  const tools: AnyAgentTool[] = [];

  tools.push({
    name: "map_search",
    description: "搜索地址或地点。支持模糊搜索和精确地址查询。",
    inputSchema: {
      type: "object",
      properties: {
        address: {
          type: "string",
          description: "要搜索的地址或地点名称",
        },
        city: {
          type: "string",
          description: "城市名称（可选，用于提高搜索精度）",
        },
      },
      required: ["address"],
    },
    handler: async (params: any) => {
      try {
        const result = await mcpClient.searchAddress(
          params.address,
          params.city
        );
        return {
          success: true,
          data: result,
        };
      } catch (error: any) {
        return {
          success: false,
          error: error.message || "搜索失败",
        };
      }
    },
  });

  tools.push({
    name: "map_geocode",
    description: "将地址转换为经纬度坐标（地理编码）。",
    inputSchema: {
      type: "object",
      properties: {
        address: {
          type: "string",
          description: "要转换的地址",
        },
        city: {
          type: "string",
          description: "城市名称（可选）",
        },
      },
      required: ["address"],
    },
    handler: async (params: any) => {
      try {
        const result = await mcpClient.geocode(params.address, params.city);
        return {
          success: true,
          data: result,
        };
      } catch (error: any) {
        return {
          success: false,
          error: error.message || "地理编码失败",
        };
      }
    },
  });

  tools.push({
    name: "map_reverse_geocode",
    description: "将经纬度坐标转换为地址（逆地理编码）。",
    inputSchema: {
      type: "object",
      properties: {
        longitude: {
          type: "number",
          description: "经度",
        },
        latitude: {
          type: "number",
          description: "纬度",
        },
      },
      required: ["longitude", "latitude"],
    },
    handler: async (params: any) => {
      try {
        const result = await mcpClient.reverseGeocode(
          params.longitude,
          params.latitude
        );
        return {
          success: true,
          data: result,
        };
      } catch (error: any) {
        return {
          success: false,
          error: error.message || "逆地理编码失败",
        };
      }
    },
  });

  tools.push({
    name: "map_route",
    description: "规划两点之间的路线。支持驾车、步行、骑行和公交路线。",
    inputSchema: {
      type: "object",
      properties: {
        origin: {
          type: "string",
          description: "起点地址或坐标",
        },
        destination: {
          type: "string",
          description: "终点地址或坐标",
        },
        mode: {
          type: "string",
          description: "出行方式",
          enum: ["driving", "walking", "bicycling", "transit"],
          default: "driving",
        },
      },
      required: ["origin", "destination"],
    },
    handler: async (params: any) => {
      try {
        const result = await mcpClient.planRoute(
          params.origin,
          params.destination,
          params.mode || "driving"
        );
        return {
          success: true,
          data: result,
        };
      } catch (error: any) {
        return {
          success: false,
          error: error.message || "路线规划失败",
        };
      }
    },
  });

  tools.push({
    name: "map_nearby",
    description: "搜索指定位置周边的设施或兴趣点（POI）。",
    inputSchema: {
      type: "object",
      properties: {
        location: {
          type: "string",
          description: "中心位置（地址或坐标）",
        },
        keywords: {
          type: "string",
          description: "搜索关键词（如：餐厅、加油站、医院等）",
        },
        radius: {
          type: "number",
          description: "搜索半径（米），默认1000米",
          default: 1000,
        },
      },
      required: ["location", "keywords"],
    },
    handler: async (params: any) => {
      try {
        const result = await mcpClient.searchNearby(
          params.location,
          params.keywords,
          params.radius
        );
        return {
          success: true,
          data: result,
        };
      } catch (error: any) {
        return {
          success: false,
          error: error.message || "周边搜索失败",
        };
      }
    },
  });

  return tools;
}
