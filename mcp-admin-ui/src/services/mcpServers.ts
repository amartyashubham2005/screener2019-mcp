import { api } from "./api";

export interface McpServer {
  id?: string;
  name: string;
  endpoint: string;
  source_ids: string[];
  created_at?: string;
  updated_at?: string;
}

// Define separate types for create and update operations
export type CreateMcpServerData = Omit<McpServer, "id" | "endpoint" | "created_at" | "updated_at">;
export type UpdateMcpServerData = Omit<McpServer, "id" | "endpoint" | "created_at" | "updated_at">;

export const mcpServersApi = {
  // Get all MCP servers
  getMcpServers: () => api.get<McpServer[]>("/api/v1/mcp-servers"),

  // Get a specific MCP server by ID
  getMcpServer: (id: string) => api.get<McpServer>(`/api/v1/mcp-servers/${id}`),

  // Create a new MCP server (endpoint not required - API generates it)
  createMcpServer: (data: CreateMcpServerData) => api.post<McpServer>("/api/v1/mcp-servers", data),

  // Update an existing MCP server (endpoint not allowed to be updated)
  updateMcpServer: (id: string, data: Partial<UpdateMcpServerData>) => 
    api.put<McpServer>(`/api/v1/mcp-servers/${id}`, data),

  // Delete an MCP server
  deleteMcpServer: (id: string) => api.delete(`/api/v1/mcp-servers/${id}`),
};
