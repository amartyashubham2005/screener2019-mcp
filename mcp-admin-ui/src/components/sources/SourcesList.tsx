import { Source } from "../../services/sources";
import { PencilIcon, TrashBinIcon, EyeIcon } from "../../icons";

interface SourcesListProps {
  sources: Source[];
  loading: boolean;
  onEdit: (source: Source) => void;
  onDelete: (id: string) => void;
  onViewDetails: (source: Source) => void;
}

export default function SourcesList({ sources, loading, onEdit, onDelete, onViewDetails }: SourcesListProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (sources.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        No sources found. Create your first source to get started.
      </div>
    );
  }

  const formatMetadata = (source: Source) => {
    if (source.type === "outlook") {
      const metadata = source.source_metadata as any;
      return (
        <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <div><span className="font-medium">Tenant:</span> {metadata.tenant_id}</div>
          <div><span className="font-medium">Client:</span> {metadata.graph_client_id}</div>
          <div><span className="font-medium">User:</span> {metadata.graph_user_id}</div>
        </div>
      );
    } else if (source.type === "snowflake") {
      const metadata = source.source_metadata as any;
      return (
        <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <div><span className="font-medium">Account:</span> {metadata.snowflake_account_url}</div>
          <div><span className="font-medium">Model:</span> {metadata.snowflake_semantic_model_file}</div>
          <div><span className="font-medium">Search:</span> {metadata.snowflake_cortex_search_service}</div>
        </div>
      );
    } else {
      const metadata = source.source_metadata as any;
      return (
        <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <div><span className="font-medium">Client:</span> {metadata.box_client_id}</div>
          <div><span className="font-medium">Subject Type:</span> {metadata.box_subject_type}</div>
          <div><span className="font-medium">Subject ID:</span> {metadata.box_subject_id}</div>
        </div>
      );
    }
  };

  const handleDelete = (id: string) => {
    if (window.confirm("Are you sure you want to delete this source? This action cannot be undone.")) {
      onDelete(id);
    }
  };

  return (
    <div className="space-y-4">
      {sources.map((source) => (
        <div
          key={source.id}
          className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow dark:border-gray-700 dark:bg-gray-800/50 cursor-pointer"
          onClick={() => onViewDetails(source)}
          title="Click to view source details"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className={`
                  inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                  ${source.type === "outlook" 
                    ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                    : source.type === "snowflake"
                    ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                    : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                  }
                `}>
                  {source.type === "outlook" ? "Outlook" : source.type === "snowflake" ? "Snowflake" : "Box"}
                </span>
                {source.created_at && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Created: {new Date(source.created_at).toLocaleDateString()}
                  </span>
                )}
              </div>
              {formatMetadata(source)}
            </div>
            <div className="flex items-center gap-2 ml-4">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onViewDetails(source);
                }}
                className="p-2 text-gray-600 hover:text-primary hover:bg-gray-100 rounded-lg transition-colors dark:text-gray-400 dark:hover:bg-gray-700"
                title="View source details"
              >
                <EyeIcon className="w-4 h-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(source);
                }}
                className="p-2 text-gray-600 hover:text-primary hover:bg-gray-100 rounded-lg transition-colors dark:text-gray-400 dark:hover:bg-gray-700"
                title="Edit source"
              >
                <PencilIcon className="w-4 h-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(source.id!);
                }}
                className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors dark:text-gray-400 dark:hover:bg-red-900/20"
                title="Delete source"
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
