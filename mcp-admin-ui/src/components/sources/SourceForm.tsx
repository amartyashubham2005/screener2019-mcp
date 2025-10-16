import { useState, useEffect } from "react";
import Label from "../form/Label";
import Input from "../form/input/InputField";
import Select from "../form/Select";
import { Source, OutlookMetadata, SnowflakeMetadata, BoxMetadata } from "../../services/sources";

interface SourceFormProps {
  initialData?: Source | null;
  onSubmit: (data: Omit<Source, "id">) => void;
  onCancel?: () => void;
}

const sourceTypeOptions = [
  { value: "outlook", label: "Outlook" },
  { value: "snowflake", label: "Snowflake" },
  { value: "box", label: "Box" },
];

export default function SourceForm({ initialData, onSubmit, onCancel }: SourceFormProps) {
  const [sourceType, setSourceType] = useState<"outlook" | "snowflake" | "box">("outlook");
  const [formData, setFormData] = useState<OutlookMetadata | SnowflakeMetadata | BoxMetadata>({
    tenant_id: "",
    graph_client_id: "",
    graph_client_secret: "",
    graph_user_id: "",
  } as OutlookMetadata);

  useEffect(() => {
    if (initialData) {
      setSourceType(initialData.type);
      setFormData(initialData.source_metadata);
    } else {
      // Reset form when not editing
      setSourceType("outlook");
      setFormData({
        tenant_id: "",
        graph_client_id: "",
        graph_client_secret: "",
        graph_user_id: "",
      } as OutlookMetadata);
    }
  }, [initialData]);

  const handleTypeChange = (value: string) => {
    const newType = value as "outlook" | "snowflake" | "box";
    setSourceType(newType);
    
    // Reset form data based on type
    if (newType === "outlook") {
      setFormData({
        tenant_id: "",
        graph_client_id: "",
        graph_client_secret: "",
        graph_user_id: "",
      } as OutlookMetadata);
    } else if (newType === "snowflake") {
      setFormData({
        snowflake_account_url: "",
        snowflake_pat: "",
        snowflake_semantic_model_file: "",
        snowflake_cortex_search_service: "",
      } as SnowflakeMetadata);
    } else {
      setFormData({
        box_client_id: "",
        box_client_secret: "",
        box_subject_type: "user",
        box_subject_id: "",
      } as BoxMetadata);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      type: sourceType,
      source_metadata: formData,
    });
    
    // Reset form if creating new source
    if (!initialData) {
      handleTypeChange(sourceType);
    }
  };

  const renderOutlookFields = () => {
    const data = formData as OutlookMetadata;
    return (
      <>
        <div>
          <Label htmlFor="tenant_id">Tenant ID</Label>
          <Input
            type="text"
            id="tenant_id"
            value={data.tenant_id}
            onChange={(e) => handleInputChange("tenant_id", e.target.value)}
            placeholder="Enter tenant ID"
          />
        </div>
        <div>
          <Label htmlFor="graph_client_id">Graph Client ID</Label>
          <Input
            type="text"
            id="graph_client_id"
            value={data.graph_client_id}
            onChange={(e) => handleInputChange("graph_client_id", e.target.value)}
            placeholder="Enter graph client ID"
          />
        </div>
        <div>
          <Label htmlFor="graph_client_secret">Graph Client Secret</Label>
          <Input
            type="password"
            id="graph_client_secret"
            value={data.graph_client_secret}
            onChange={(e) => handleInputChange("graph_client_secret", e.target.value)}
            placeholder="Enter graph client secret"
          />
        </div>
        <div>
          <Label htmlFor="graph_user_id">Graph User ID</Label>
          <Input
            type="text"
            id="graph_user_id"
            value={data.graph_user_id}
            onChange={(e) => handleInputChange("graph_user_id", e.target.value)}
            placeholder="Enter graph user ID"
          />
        </div>
      </>
    );
  };

  const renderSnowflakeFields = () => {
    const data = formData as SnowflakeMetadata;
    return (
      <>
        <div>
          <Label htmlFor="snowflake_account_url">Account URL</Label>
          <Input
            type="url"
            id="snowflake_account_url"
            value={data.snowflake_account_url}
            onChange={(e) => handleInputChange("snowflake_account_url", e.target.value)}
            placeholder="https://your-account.snowflakecomputing.com"
          />
        </div>
        <div>
          <Label htmlFor="snowflake_pat">Personal Access Token</Label>
          <Input
            type="password"
            id="snowflake_pat"
            value={data.snowflake_pat}
            onChange={(e) => handleInputChange("snowflake_pat", e.target.value)}
            placeholder="Enter PAT token"
          />
        </div>
        <div>
          <Label htmlFor="snowflake_semantic_model_file">Semantic Model File</Label>
          <Input
            type="text"
            id="snowflake_semantic_model_file"
            value={data.snowflake_semantic_model_file}
            onChange={(e) => handleInputChange("snowflake_semantic_model_file", e.target.value)}
            placeholder="model.yaml"
          />
        </div>
        <div>
          <Label htmlFor="snowflake_cortex_search_service">Cortex Search Service</Label>
          <Input
            type="text"
            id="snowflake_cortex_search_service"
            value={data.snowflake_cortex_search_service}
            onChange={(e) => handleInputChange("snowflake_cortex_search_service", e.target.value)}
            placeholder="Enter search service name"
          />
        </div>
      </>
    );
  };

  const renderBoxFields = () => {
    const data = formData as BoxMetadata;
    return (
      <>
        <div>
          <Label htmlFor="box_client_id">Box Client ID</Label>
          <Input
            type="text"
            id="box_client_id"
            value={data.box_client_id}
            onChange={(e) => handleInputChange("box_client_id", e.target.value)}
            placeholder="Enter Box client ID"
          />
        </div>
        <div>
          <Label htmlFor="box_client_secret">Box Client Secret</Label>
          <Input
            type="password"
            id="box_client_secret"
            value={data.box_client_secret}
            onChange={(e) => handleInputChange("box_client_secret", e.target.value)}
            placeholder="Enter Box client secret"
          />
        </div>
        <div>
          <Label htmlFor="box_subject_type">Subject Type</Label>
          <Input
            type="text"
            id="box_subject_type"
            value={data.box_subject_type}
            onChange={(e) => handleInputChange("box_subject_type", e.target.value)}
            placeholder="user"
          />
        </div>
        <div>
          <Label htmlFor="box_subject_id">Subject ID</Label>
          <Input
            type="text"
            id="box_subject_id"
            value={data.box_subject_id}
            onChange={(e) => handleInputChange("box_subject_id", e.target.value)}
            placeholder="Enter subject ID"
          />
        </div>
      </>
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <Label>Source Type</Label>
        <Select
          key={sourceType} // Force re-render when type changes
          options={sourceTypeOptions}
          placeholder="Select source type"
          defaultValue={sourceType}
          onChange={handleTypeChange}
          className="dark:bg-dark-900"
        />
      </div>

      {sourceType === "outlook" ? renderOutlookFields() : 
       sourceType === "snowflake" ? renderSnowflakeFields() : renderBoxFields()}

      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          className="flex-1 rounded-lg bg-brand-500 px-6 py-3 text-sm font-medium text-white hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 shadow-theme-xs transition"
        >
          {initialData ? "Update Source" : "Create Source"}
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
