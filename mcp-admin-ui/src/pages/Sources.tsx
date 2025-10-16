import { useState, useEffect } from "react";
import PageBreadcrumb from "../components/common/PageBreadCrumb";
import ComponentCard from "../components/common/ComponentCard";
import PageMeta from "../components/common/PageMeta";
import SourceForm from "../components/sources/SourceForm";
import SourcesList from "../components/sources/SourcesList";
import SourceDetailsModal from "../components/sources/SourceDetailsModal";
import { sourcesApi, Source } from "../services/sources";

export type { Source, OutlookMetadata, SnowflakeMetadata, BoxMetadata } from "../services/sources";
import toast from "react-hot-toast";

export default function Sources() {
  const [sources, setSources] = useState<Source[]>([]);
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [viewingSource, setViewingSource] = useState<Source | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchSources = async () => {
    try {
      setLoading(true);
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
      setLoading(false);
    }
  };

  const handleCreateSource = async (sourceData: Omit<Source, "id">) => {
    try {
      const response = await sourcesApi.createSource(sourceData);
      if (response.ok) {
        toast.success("Source created successfully");
        fetchSources();
      } else {
        toast.error("Failed to create source");
      }
    } catch (error) {
      toast.error("Error creating source");
      console.error("Error creating source:", error);
    }
  };

  const handleUpdateSource = async (id: string, sourceData: Omit<Source, "id">) => {
    try {
      const response = await sourcesApi.updateSource(id, sourceData);
      if (response.ok) {
        toast.success("Source updated successfully");
        setEditingSource(null);
        fetchSources();
      } else {
        toast.error("Failed to update source");
      }
    } catch (error) {
      toast.error("Error updating source");
      console.error("Error updating source:", error);
    }
  };

  const handleDeleteSource = async (id: string) => {
    try {
      const response = await sourcesApi.deleteSource(id);
      if (response.ok) {
        toast.success("Source deleted successfully");
        fetchSources();
      } else {
        toast.error("Failed to delete source");
      }
    } catch (error) {
      toast.error("Error deleting source");
      console.error("Error deleting source:", error);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  return (
    <>
      <PageMeta
        title="MCP Admin UI Sources Dashboard | MCP Admin UI : LLM-Powered OBM ABC Analysis Tool"
        description="This is MCP Admin UI Sources Dashboard page for MCP Admin UI - LLM-Powered OBM ABC Analysis Tool"
      />
      <PageBreadcrumb pageTitle="Sources" />
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="space-y-6">
          <ComponentCard title={editingSource ? "Edit Source" : "Add New Source"}>
            <SourceForm
              initialData={editingSource}
              onSubmit={editingSource 
                ? (data: Omit<Source, "id">) => handleUpdateSource(editingSource.id!, data)
                : handleCreateSource
              }
              onCancel={() => setEditingSource(null)}
            />
          </ComponentCard>
        </div>
        <div className="space-y-6">
          <ComponentCard title="Sources List">
            <SourcesList
              sources={sources}
              loading={loading}
              onEdit={setEditingSource}
              onDelete={handleDeleteSource}
              onViewDetails={setViewingSource}
            />
          </ComponentCard>
        </div>
      </div>

      {/* Source Details Modal */}
      <SourceDetailsModal
        isOpen={!!viewingSource}
        onClose={() => setViewingSource(null)}
        source={viewingSource}
      />
    </>
  );
}
