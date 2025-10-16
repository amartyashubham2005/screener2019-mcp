import { useState, useEffect } from "react";
import PageBreadcrumb from "../components/common/PageBreadCrumb";
import ComponentCard from "../components/common/ComponentCard";
import PageMeta from "../components/common/PageMeta";
import McpServerForm from "../components/mcp-servers/McpServerForm";
import McpServersList from "../components/mcp-servers/McpServersList";
import McpServerDetailsModal from "../components/mcp-servers/McpServerDetailsModal";
import { mcpServersApi, McpServer, CreateMcpServerData, UpdateMcpServerData } from "../services/mcpServers";
import { sourcesApi, Source } from "../services/sources";
import toast from "react-hot-toast";

export type { McpServer } from "../services/mcpServers";

export default function McpServers() {
  const [mcpServers, setMcpServers] = useState<McpServer[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [editingServer, setEditingServer] = useState<McpServer | null>(null);
  const [viewingServer, setViewingServer] = useState<McpServer | null>(null);
  const [loading, setLoading] = useState(false);
  const [sourcesLoading, setSourcesLoading] = useState(false);

  const fetchMcpServers = async () => {
    try {
      setLoading(true);
      const response = await mcpServersApi.getMcpServers();
      if (response.ok) {
        setMcpServers(response.data || []);
      } else {
        toast.error("Failed to fetch MCP servers");
      }
    } catch (error) {
      toast.error("Error fetching MCP servers");
      console.error("Error fetching MCP servers:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSources = async () => {
    try {
      setSourcesLoading(true);
      const response = await sourcesApi.getSources();
      if (response.ok) {
        setSources(response.data || []);
      } else {
        toast.error("Failed to fetch sources");
      }
    } catch (error) {
      toast.error("Error fetching sources");
      console.error("Error fetching sources:", error);
    } finally {
      setSourcesLoading(false);
    }
  };

  const handleCreateServer = async (serverData: CreateMcpServerData) => {
    try {
      const response = await mcpServersApi.createMcpServer(serverData);
      if (response.ok) {
        toast.success("MCP server created successfully");
        fetchMcpServers();
      } else {
        toast.error("Failed to create MCP server");
      }
    } catch (error) {
      toast.error("Error creating MCP server");
      console.error("Error creating MCP server:", error);
    }
  };

  const handleUpdateServer = async (id: string, serverData: Partial<UpdateMcpServerData>) => {
    try {
      const response = await mcpServersApi.updateMcpServer(id, serverData);
      if (response.ok) {
        toast.success("MCP server updated successfully");
        setEditingServer(null);
        fetchMcpServers();
      } else {
        toast.error("Failed to update MCP server");
      }
    } catch (error) {
      toast.error("Error updating MCP server");
      console.error("Error updating MCP server:", error);
    }
  };

  type UpsertPayload = CreateMcpServerData | Partial<UpdateMcpServerData>;

  const handleUpsert = (data: UpsertPayload) => {
    if (editingServer) {
      return handleUpdateServer(editingServer.id!, data as Partial<UpdateMcpServerData>);
    }
    return handleCreateServer(data as CreateMcpServerData);
  };

  const handleDeleteServer = async (id: string) => {
    try {
      const response = await mcpServersApi.deleteMcpServer(id);
      if (response.ok) {
        toast.success("MCP server deleted successfully");
        fetchMcpServers();
      } else {
        toast.error("Failed to delete MCP server");
      }
    } catch (error) {
      toast.error("Error deleting MCP server");
      console.error("Error deleting MCP server:", error);
    }
  };

  useEffect(() => {
    fetchMcpServers();
    fetchSources();
  }, []);

  return (
    <>
      <PageMeta
        title="MCP Admin UI MCP Servers Dashboard | MCP Admin UI : LLM-Powered OBM ABC Analysis Tool"
        description="This is MCP Admin UI MCP Servers Dashboard page for MCP Admin UI - LLM-Powered OBM ABC Analysis Tool"
      />
      <PageBreadcrumb pageTitle="MCP Servers" />
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="space-y-6">
          <ComponentCard title={editingServer ? "Edit MCP Server" : "Add New MCP Server"}>
            <McpServerForm
              initialData={editingServer}
              sources={sources}
              sourcesLoading={sourcesLoading}
              onSubmit={handleUpsert}
              onCancel={() => setEditingServer(null)}
            />
          </ComponentCard>
        </div>
        <div className="space-y-6">
          <ComponentCard title="MCP Servers List">
            <McpServersList
              mcpServers={mcpServers}
              sources={sources}
              loading={loading}
              onEdit={setEditingServer}
              onDelete={handleDeleteServer}
              onViewDetails={setViewingServer}
            />
          </ComponentCard>
        </div>
      </div>

      {/* MCP Server Details Modal */}
      <McpServerDetailsModal
        isOpen={!!viewingServer}
        onClose={() => setViewingServer(null)}
        server={viewingServer}
        sources={sources}
      />
    </>
  );
}
