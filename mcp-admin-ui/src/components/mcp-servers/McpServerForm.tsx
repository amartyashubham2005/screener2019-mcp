import { useState, useEffect } from "react";
import Label from "../form/Label";
import Input from "../form/input/InputField";
import { McpServer, CreateMcpServerData, UpdateMcpServerData } from "../../services/mcpServers";
import { Source } from "../../services/sources";

interface McpServerFormProps {
  initialData?: McpServer | null;
  sources: Source[];
  sourcesLoading: boolean;
  onSubmit: (data: CreateMcpServerData | Partial<UpdateMcpServerData>) => void | Promise<void>;
  onCancel?: () => void;
}

export default function McpServerForm({ 
  initialData, 
  sources, 
  sourcesLoading, 
  onSubmit, 
  onCancel 
}: McpServerFormProps) {
  const [formData, setFormData] = useState({
    name: "",
    source_ids: [] as string[],
  });

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name,
        source_ids: initialData.source_ids || [],
      });
    } else {
      // Reset form when not editing
      setFormData({
        name: "",
        source_ids: [],
      });
    }
  }, [initialData]);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSourceToggle = (sourceId: string) => {
    setFormData(prev => ({
      ...prev,
      source_ids: prev.source_ids.includes(sourceId)
        ? prev.source_ids.filter(id => id !== sourceId)
        : [...prev.source_ids, sourceId]
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
    
    // Reset form if creating new server
    if (!initialData) {
      setFormData({
        name: "",
        source_ids: [],
      });
    }
  };

  const getSourceDisplayName = (source: Source) => {
    if (source.type === "outlook") {
      const metadata = source.source_metadata as any;
      return `${source.type.toUpperCase()} - ${metadata.graph_user_id || metadata.tenant_id}`;
    } else if (source.type === "snowflake") {
      const metadata = source.source_metadata as any;
      return `${source.type.toUpperCase()} - ${metadata.snowflake_account_url}`;
    } else if (source.type === "box") {
      const metadata = source.source_metadata as any;
      return `${source.type.toUpperCase()} - ${metadata.box_subject_id}`;
    }
    return "UNKNOWN";
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <Label htmlFor="name">Server Name</Label>
        <Input
          type="text"
          id="name"
          value={formData.name}
          onChange={(e) => handleInputChange("name", e.target.value)}
          placeholder="Enter server name"
        />
      </div>

      {/* Only show endpoint field in edit mode (read-only) */}
      {initialData && (
        <div>
          <Label htmlFor="endpoint">Endpoint URL</Label>
          <Input
            type="text"
            id="endpoint"
            value={`https://${initialData.endpoint}/sse`}
            placeholder="Endpoint will be generated automatically"
            disabled
          />
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Endpoint is automatically generated and cannot be modified
          </div>
        </div>
      )}

      <div>
        <Label>Sources (Optional)</Label>
        {sourcesLoading ? (
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-500"></div>
          </div>
        ) : sources.length === 0 ? (
          <div className="text-sm text-gray-500 dark:text-gray-400 py-2">
            No sources available. Create sources first to assign them to this server.
          </div>
        ) : (
          <div className="space-y-3 border border-gray-200 dark:border-gray-700 rounded-lg p-4 max-h-48 overflow-y-auto">
            {sources.map((source) => (
              <label
                key={source.id}
                className="flex items-center space-x-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 p-2 rounded"
              >
                <input
                  type="checkbox"
                  checked={formData.source_ids.includes(source.id!)}
                  onChange={() => handleSourceToggle(source.id!)}
                  className="h-4 w-4 text-brand-500 focus:ring-brand-500 border-gray-300 rounded"
                />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {getSourceDisplayName(source)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    ID: {source.id}
                  </div>
                </div>
                <span className={`
                  inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                  ${source.type === "outlook" 
                    ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                    : source.type === "snowflake"
                    ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                    : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                  }
                `}>
                  {source.type}
                </span>
              </label>
            ))}
          </div>
        )}
        <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Selected: {formData.source_ids.length} source(s)
        </div>
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          className="flex-1 rounded-lg bg-brand-500 px-6 py-3 text-sm font-medium text-white hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 shadow-theme-xs transition"
        >
          {initialData ? "Update Server" : "Create Server"}
        </button>
        {initialData && onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 rounded-lg border border-gray-300 px-6 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800 shadow-theme-xs transition"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
