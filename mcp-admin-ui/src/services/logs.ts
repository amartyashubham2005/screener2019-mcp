import { api } from "./api";

export interface LogEntry {
  id: string;
  text: string;
  ts: number;
  level: string;
  operation?: string;
  method?: string;
  status?: string;
  correlation_id?: string;
  elapsed_sec?: number;
  log_metadata?: Record<string, any>;
  created_at: string;
}

export interface LogsResponse {
  logs: LogEntry[];
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface LogStats {
  total_operations: number;
  by_operation: Record<string, number>;
  by_status: Record<string, number>;
  failed_count: number;
  success_count: number;
  avg_elapsed_sec: number;
}

export const logsApi = {
  // Get logs with pagination and filters
  getLogs: (params?: {
    limit?: number;
    offset?: number;
    operation?: string;
    level?: string;
    correlation_id?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append("limit", params.limit.toString());
    if (params?.offset) searchParams.append("offset", params.offset.toString());
    if (params?.operation) searchParams.append("operation", params.operation);
    if (params?.level) searchParams.append("level", params.level);
    if (params?.correlation_id) searchParams.append("correlation_id", params.correlation_id);

    return api.get<LogsResponse>(`/api/v1/logs?${searchParams.toString()}`);
  },

  // Get operation statistics
  getStats: (hours?: number) => {
    const searchParams = new URLSearchParams();
    if (hours) searchParams.append("hours", hours.toString());

    return api.get<LogStats>(`/api/v1/logs/stats?${searchParams.toString()}`);
  },
};
