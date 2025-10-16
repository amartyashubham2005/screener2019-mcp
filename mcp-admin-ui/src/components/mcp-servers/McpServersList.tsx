import { McpServer } from "../../services/mcpServers";
import { Source } from "../../services/sources";
import { PencilIcon, TrashBinIcon, PlugInIcon, EyeIcon } from "../../icons";

interface McpServersListProps {
  mcpServers: McpServer[];
  sources: Source[];
  loading: boolean;
  onEdit: (server: McpServer) => void;
  onDelete: (id: string) => void;
  onViewDetails: (server: McpServer) => void;
}

export default function McpServersList({ 
  mcpServers, 
  sources, 
  loading, 
  onEdit, 
  onDelete,
  onViewDetails 
}: McpServersListProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500"></div>
      </div>
    );
  }

  if (mcpServers.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        No MCP servers found. Create your first MCP server to get started.
      </div>
    );
  }

  const getSourceById = (sourceId: string) => {
    console.log('sources', sources);
    console.log('sourceId', sourceId);
    return sources.find(source => source.id === sourceId);
  };

  const formatSourcesList = (sourceIds: string[]) => {
    if (sourceIds.length === 0) {
      return (
        <span className="text-gray-400 dark:text-gray-500 italic text-sm">
          No sources assigned
        </span>
      );
    }

    return (
      <div className="flex flex-wrap gap-1">
        {sourceIds.map((sourceId) => {
          const source = getSourceById(sourceId);
          if (!source) {
            return (
              <span 
                key={sourceId}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
              >
                Unknown Source
              </span>
            );
          }

          return (
            <span
              key={sourceId}
              className={`
                inline-flex items-center px-2 py-1 rounded-full text-xs font-medium cursor-pointer hover:opacity-80 transition-opacity
                ${source.type === "outlook" 
                  ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                  : source.type === "snowflake"
                  ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                  : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                }
              `}
              onClick={(e) => {
                e.stopPropagation();
                // We'll handle source click in the parent component
              }}
              title={`Click to view ${source.type} source details`}
            >
              {source.type}
            </span>
          );
        })}
      </div>
    );
  };

  const handleDelete = (id: string) => {
    if (window.confirm("Are you sure you want to delete this MCP server? This action cannot be undone.")) {
      onDelete(id);
    }
  };

  return (
    <div className="space-y-4">
      {mcpServers.map((server) => (
        <div
          key={server.id}
          className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow dark:border-gray-700 dark:bg-gray-800/50 cursor-pointer"
          onClick={() => onViewDetails(server)}
          title="Click to view server details"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <PlugInIcon className="w-4 h-4 text-brand-500" />
                <h3 className="text-base font-medium text-gray-900 dark:text-gray-100">
                  {server.name}
                </h3>
                {server.created_at && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Created: {new Date(server.created_at).toLocaleDateString()}
                  </span>
                )}
              </div>
              
              <div className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <div>
                  <span className="font-medium">Endpoint:</span>{" "}
                  <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                    https://{server.endpoint}/sse
                  </span>
                </div>
                
                <div>
                  <span className="font-medium">Sources ({server.source_ids?.length || 0}):</span>
                  <div className="mt-1">
                    {formatSourcesList(server.source_ids || [])}
                  </div>
                </div>

                {server.id && (
                  <div className="text-xs text-gray-400 dark:text-gray-500">
                    ID: {server.id}
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-2 ml-4">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onViewDetails(server);
                }}
                className="p-2 text-gray-600 hover:text-brand-500 hover:bg-gray-100 rounded-lg transition-colors dark:text-gray-400 dark:hover:bg-gray-700"
                title="View server details"
              >
                <EyeIcon className="w-4 h-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(server);
                }}
                className="p-2 text-gray-600 hover:text-brand-500 hover:bg-gray-100 rounded-lg transition-colors dark:text-gray-400 dark:hover:bg-gray-700"
                title="Edit MCP server"
              >
                <PencilIcon className="w-4 h-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(server.id!);
                }}
                className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors dark:text-gray-400 dark:hover:bg-red-900/20"
                title="Delete MCP server"
              >
                <TrashBinIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
