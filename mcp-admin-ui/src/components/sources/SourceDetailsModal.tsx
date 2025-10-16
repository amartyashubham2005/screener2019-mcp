import { Modal } from "../ui/modal";
import { Source } from "../../services/sources";

interface SourceDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  source: Source | null;
}

export default function SourceDetailsModal({
  isOpen,
  onClose,
  source
}: SourceDetailsModalProps) {
  if (!source) return null;

  const formatMetadata = (source: Source) => {
    if (source.type === "outlook") {
      const metadata = source.source_metadata as any;
      return [
        { label: "Tenant ID", value: metadata.tenant_id },
        { label: "Graph Client ID", value: metadata.graph_client_id },
        { label: "Graph Client Secret", value: "•".repeat(20), isSensitive: true },
        { label: "Graph User ID", value: metadata.graph_user_id },
      ];
    } else if (source.type === "snowflake") {
      const metadata = source.source_metadata as any;
      return [
        { label: "Account URL", value: metadata.snowflake_account_url },
        { label: "Personal Access Token", value: "•".repeat(20), isSensitive: true },
        { label: "Semantic Model File", value: metadata.snowflake_semantic_model_file },
        { label: "Cortex Search Service", value: metadata.snowflake_cortex_search_service },
      ];
    } else if (source.type === "box") {
      const metadata = source.source_metadata as any;
      return [
        { label: "Box Client ID", value: metadata.box_client_id },
        { label: "Box Client Secret", value: "•".repeat(20), isSensitive: true },
        { label: "Subject Type", value: metadata.box_subject_type },
        { label: "Subject ID", value: metadata.box_subject_id },
      ];
    }
    return [];
  };

  const metadataFields = formatMetadata(source);

  const getSourceIcon = (type: string) => {
    switch (type) {
      case "outlook":
        return "📧";
      case "snowflake":
        return "❄️";
      case "box":
        return "📦";
      default:
        return "🔗";
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-2xl mx-4">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
          <span className="text-2xl">{getSourceIcon(source.type)}</span>
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Source Details
            </h2>
            <span className={`
              inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1
              ${source.type === "outlook" 
                ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                : source.type === "snowflake"
                ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
              }
            `}>
              {source.type.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Basic Info */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Source ID</label>
            <div className="mt-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <span className="text-gray-600 dark:text-gray-400 font-mono text-sm">{source.id}</span>
            </div>
          </div>

          {source.created_at && (
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Created</label>
              <div className="mt-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-600 dark:text-gray-400">
                  {new Date(source.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          )}

          {source.updated_at && (
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Last Updated</label>
              <div className="mt-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-600 dark:text-gray-400">
                  {new Date(source.updated_at).toLocaleString()}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Metadata Section */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
            Configuration Details
          </h3>
          
          <div className="space-y-3">
            {metadataFields.map((field, index) => (
              <div key={index} className="grid grid-cols-3 gap-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="font-medium text-gray-700 dark:text-gray-300">
                  {field.label}:
                </div>
                <div className="col-span-2">
                  <span className={`
                    ${field.isSensitive 
                      ? "text-gray-400 dark:text-gray-500 font-mono text-sm" 
                      : "text-gray-600 dark:text-gray-400"
                    }
                    break-all
                  `}>
                    {field.value}
                  </span>
                  {field.isSensitive && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Sensitive data is hidden for security
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
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