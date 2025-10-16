import { Modal } from "../ui/modal";
import { McpServer } from "../../services/mcpServers";
import { Source } from "../../services/sources";
import { PlugInIcon } from "../../icons";

interface McpServerDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  server: McpServer | null;
  sources: Source[];
}

export default function McpServerDetailsModal({
  isOpen,
  onClose,
  server,
  sources
}: McpServerDetailsModalProps) {
  if (!server) return null;

  const getSourceById = (sourceId: string) => {
    return sources.find(source => source.id === sourceId);
  };

  const formatSourceMetadata = (source: Source) => {
    if (source.type === "outlook") {
      const metadata = source.source_metadata as any;
      return (
        <div className="space-y-2">
          <div><span className="font-medium text-gray-700 dark:text-gray-300">Tenant ID:</span> <span className="text-gray-600 dark:text-gray-400">{metadata.tenant_id}</span></div>
          <div><span className="font-medium text-gray-700 dark:text-gray-300">Client ID:</span> <span className="text-gray-600 dark:text-gray-400">{metadata.graph_client_id}</span></div>
          <div><span className="font-medium text-gray-700 dark:text-gray-300">User ID:</span> <span className="text-gray-600 dark:text-gray-400">{metadata.graph_user_id}</span></div>
        </div>
      );
    } else if (source.type === "snowflake") {
      const metadata = source.source_metadata as any;
      return (
        <div className="space-y-2">
          <div><span className="font-medium text-gray-700 dark:text-gray-300">Account URL:</span> <span className="text-gray-600 dark:text-gray-400">{metadata.snowflake_account_url}</span></div>
          <div><span className="font-medium text-gray-700 dark:text-gray-300">Semantic Model:</span> <span className="text-gray-600 dark:text-gray-400">{metadata.snowflake_semantic_model_file}</span></div>
          <div><span className="font-medium text-gray-700 dark:text-gray-300">Search Service:</span> <span className="text-gray-600 dark:text-gray-400">{metadata.snowflake_cortex_search_service}</span></div>
        </div>
      );
    } else if (source.type === "box") {
      const metadata = source.source_metadata as any;
      return (
        <div className="space-y-2">
          <div><span className="font-medium text-gray-700 dark:text-gray-300">Client ID:</span> <span className="text-gray-600 dark:text-gray-400">{metadata.box_client_id}</span></div>
          <div><span className="font-medium text-gray-700 dark:text-gray-300">Subject Type:</span> <span className="text-gray-600 dark:text-gray-400">{metadata.box_subject_type}</span></div>
          <div><span className="font-medium text-gray-700 dark:text-gray-300">Subject ID:</span> <span className="text-gray-600 dark:text-gray-400">{metadata.box_subject_id}</span></div>
        </div>
      );
    }
    return null;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-4xl mx-4">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
          <PlugInIcon className="w-6 h-6 text-brand-500" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            MCP Server Details
          </h2>
        </div>

        {/* Server Basic Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Server Name</label>
              <div className="mt-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-900 dark:text-gray-100 font-medium">{server.name}</span>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Server ID</label>
              <div className="mt-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-600 dark:text-gray-400 font-mono text-sm">{server.id}</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Endpoint URL</label>
              <div className="mt-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-600 dark:text-gray-400 font-mono text-sm break-all">
                  https://{server.endpoint}/sse
                </span>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Created</label>
              <div className="mt-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-600 dark:text-gray-400">
                  {server.created_at ? new Date(server.created_at).toLocaleString() : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Sources Section */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
            Associated Sources ({server.source_ids?.length || 0})
          </h3>
          
          {!server.source_ids || server.source_ids.length === 0 ? (
            <div className="p-6 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
              <span className="text-gray-500 dark:text-gray-400 italic">
                No sources are associated with this server
              </span>
            </div>
          ) : (
            <div className="space-y-4">
              {server.source_ids.map((sourceId) => {
                const source = getSourceById(sourceId);
                
                if (!source) {
                  return (
                    <div key={sourceId} className="p-4 border border-red-200 dark:border-red-800 rounded-lg bg-red-50 dark:bg-red-900/20">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                          Unknown Source
                        </span>
                        <span className="text-red-600 dark:text-red-400 font-mono text-sm">ID: {sourceId}</span>
                      </div>
                    </div>
                  );
                }

                return (
                  <div key={sourceId} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className={`
                          inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                          ${source.type === "outlook" 
                            ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                            : source.type === "snowflake"
                            ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                            : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                          }
                        `}>
                          {source.type.toUpperCase()}
                        </span>
                        <span className="text-gray-500 dark:text-gray-400 font-mono text-xs">
                          ID: {source.id}
                        </span>
                      </div>
                    </div>

                    <div className="text-sm">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Metadata:</h4>
                      {formatSourceMetadata(source)}
                    </div>

                    {source.created_at && (
                      <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          Created: {new Date(source.created_at).toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}