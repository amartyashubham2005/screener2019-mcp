import { useState, useEffect, useRef, useCallback } from "react";
import PageBreadcrumb from "../components/common/PageBreadCrumb";
import ComponentCard from "../components/common/ComponentCard";
import PageMeta from "../components/common/PageMeta";
import { logsApi, LogEntry } from "../services/logs";
import toast from "react-hot-toast";

export default function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [operationFilter, setOperationFilter] = useState<string>("");
  const [levelFilter, setLevelFilter] = useState<string>("");

  const observerTarget = useRef<HTMLDivElement>(null);
  const limit = 10;

  const fetchLogs = async (currentOffset: number, isLoadMore: boolean = false) => {
    if (loading) return;

    try {
      setLoading(true);
      const response = await logsApi.getLogs({
        limit,
        offset: currentOffset,
        operation: operationFilter || undefined,
        level: levelFilter || undefined,
      });

      if (response.ok && response.data) {
        if (isLoadMore) {
          setLogs((prev) => [...prev, ...response.data.logs]);
        } else {
          setLogs(response.data.logs);
        }
        setHasMore(response.data.has_more);
        setOffset(currentOffset + response.data.logs.length);
      } else {
        toast.error("Failed to fetch logs");
      }
    } catch (error) {
      toast.error("Error fetching logs");
      console.error("Error fetching logs:", error);
    } finally {
      setLoading(false);
    }
  };

  // Load more logs when scrolling
  const loadMore = useCallback(() => {
    if (hasMore && !loading) {
      fetchLogs(offset, true);
    }
  }, [offset, hasMore, loading, operationFilter, levelFilter]);

  // Setup intersection observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [loadMore, hasMore, loading]);

  // Initial load
  useEffect(() => {
    setOffset(0);
    fetchLogs(0, false);
  }, [operationFilter, levelFilter]);

  const formatTimestamp = (ts: number) => {
    const date = new Date(ts);
    return date.toLocaleString();
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "SUCCESS":
        return "text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20";
      case "FAILED":
        return "text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20";
      case "START":
        return "text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20";
      case "IN_PROGRESS":
        return "text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20";
      case "WARNING":
        return "text-orange-600 bg-orange-50 dark:text-orange-400 dark:bg-orange-900/20";
      default:
        return "text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-900/20";
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "ERROR":
        return "text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20";
      case "WARNING":
        return "text-orange-600 bg-orange-50 dark:text-orange-400 dark:bg-orange-900/20";
      case "INFO":
        return "text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20";
      default:
        return "text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-900/20";
    }
  };

  return (
    <>
      <PageMeta
        title="MCP Admin UI Logs Dashboard | MCP Admin UI"
        description="View and monitor MCP operation logs"
      />
      <PageBreadcrumb pageTitle="Logs" />

      <div className="space-y-6">
        {/* Filters */}
        <ComponentCard title="Filters">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Operation
              </label>
              <select
                value={operationFilter}
                onChange={(e) => setOperationFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
              >
                <option value="">All Operations</option>
                <option value="SEARCH">SEARCH</option>
                <option value="FETCH">FETCH</option>
                <option value="AUTH">AUTH</option>
                <option value="CRUD">CRUD</option>
                <option value="HEALTH">HEALTH</option>
                <option value="HANDLER_INIT">HANDLER_INIT</option>
                <option value="DB_QUERY">DB_QUERY</option>
                <option value="API_CALL">API_CALL</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Level
              </label>
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
              >
                <option value="">All Levels</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
              </select>
            </div>
          </div>
        </ComponentCard>

        {/* Logs List */}
        <ComponentCard title={`Logs (${logs.length} entries)`}>
          <div className="space-y-3">
            {logs.length === 0 && !loading && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No logs found
              </div>
            )}

            {logs.map((log) => (
              <div
                key={log.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${getLevelColor(
                        log.level
                      )}`}
                    >
                      {log.level}
                    </span>
                    {log.operation && (
                      <span className="px-2 py-1 rounded text-xs font-medium bg-indigo-50 text-indigo-600 dark:bg-indigo-900/20 dark:text-indigo-400">
                        {log.operation}
                      </span>
                    )}
                    {log.status && (
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
                          log.status
                        )}`}
                      >
                        {log.status}
                      </span>
                    )}
                    {log.elapsed_sec !== null && log.elapsed_sec !== undefined && (
                      <span className="px-2 py-1 rounded text-xs font-medium bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400">
                        {log.elapsed_sec.toFixed(3)}s
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                    {formatTimestamp(log.ts)}
                  </span>
                </div>

                <div className="mb-2">
                  <p className="text-sm text-gray-900 dark:text-gray-100 font-mono break-all">
                    {log.text}
                  </p>
                </div>

                {(log.method || log.correlation_id) && (
                  <div className="flex items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
                    {log.method && (
                      <span>
                        <span className="font-medium">Method:</span> {log.method}
                      </span>
                    )}
                    {log.correlation_id && (
                      <span>
                        <span className="font-medium">Correlation:</span>{" "}
                        {log.correlation_id}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}

            {/* Loading indicator */}
            {loading && (
              <div className="text-center py-4">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  Loading logs...
                </p>
              </div>
            )}

            {/* Infinite scroll trigger */}
            {hasMore && !loading && (
              <div ref={observerTarget} className="h-4" />
            )}

            {/* End of logs message */}
            {!hasMore && logs.length > 0 && (
              <div className="text-center py-4 text-sm text-gray-500 dark:text-gray-400">
                No more logs to load
              </div>
            )}
          </div>
        </ComponentCard>
      </div>
    </>
  );
}
