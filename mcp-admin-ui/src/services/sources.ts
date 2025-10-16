import { api } from "./api";

export interface Source {
  id?: string;
  type: "outlook" | "snowflake" | "box";
  source_metadata: OutlookMetadata | SnowflakeMetadata | BoxMetadata;
  created_at?: string;
  updated_at?: string;
}

export interface OutlookMetadata {
  tenant_id: string;
  graph_client_id: string;
  graph_client_secret: string;
  graph_user_id: string;
}

export interface SnowflakeMetadata {
  snowflake_account_url: string;
  snowflake_pat: string;
  snowflake_semantic_model_file: string;
  snowflake_cortex_search_service: string;
}

export interface BoxMetadata {
  box_client_id: string;
  box_client_secret: string;
  box_subject_type: string;
  box_subject_id: string;
}

export const sourcesApi = {
  // Get all sources
  getSources: () => api.get<Source[]>("/api/v1/sources"),

  // Get a specific source by ID
  getSource: (id: string) => api.get<Source>(`/api/v1/sources/${id}`),

  // Create a new source
  createSource: (data: Omit<Source, "id">) => api.post<Source>("/api/v1/sources", data),

  // Update an existing source
  updateSource: (id: string, data: Omit<Source, "id">) => 
    api.put<Source>(`/api/v1/sources/${id}`, data),

  // Delete a source
  deleteSource: (id: string) => api.delete(`/api/v1/sources/${id}`),
};
