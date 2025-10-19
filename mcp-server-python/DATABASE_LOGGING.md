# Database Logging Setup

This document describes the database logging feature that persists MCP operation logs to PostgreSQL.

## Overview

All MCP logs are now stored in both:
1. **Console/File** - Traditional text logs via Python logging
2. **Database** - Structured logs in PostgreSQL `logs` table

## Database Schema

The `logs` table stores structured log entries with the following fields:

| Column | Type | Description | Required |
|--------|------|-------------|----------|
| `id` | UUID | Primary key | Yes |
| `text` | TEXT | Full log message text | Yes |
| `user_id` | UUID | Foreign key to users table | No |
| `source_id` | UUID | Foreign key to sources table | No |
| `ts` | BIGINT | Timestamp in epoch milliseconds | Yes |
| `level` | STRING | Log level (INFO, WARNING, ERROR) | Yes |
| `operation` | STRING | Operation type (SEARCH, FETCH, AUTH, CRUD, etc.) | No |
| `method` | STRING | Method/handler name | No |
| `status` | STRING | Status (START, SUCCESS, FAILED, IN_PROGRESS) | No |
| `correlation_id` | STRING | Correlation ID for request tracing | No |
| `elapsed_sec` | FLOAT | Elapsed time in seconds | No |
| `metadata` | JSONB | Additional metadata as JSON | No |
| `created_at` | TIMESTAMP | Row creation timestamp | Yes |

### Indexes

For performance, the following indexes are created:
- `ix_logs_user_id` - Filter logs by user
- `ix_logs_source_id` - Filter logs by source
- `ix_logs_ts` - Time-based queries
- `ix_logs_correlation_id` - Trace requests
- `ix_logs_operation` - Filter by operation type
- `ix_logs_level` - Filter by log level

## Migration

Run the migration to create the logs table:

```bash
cd mcp-server-python
alembic upgrade head
```

This will create the `logs` table with all necessary indexes and foreign keys.

## How It Works

### Automatic Logging

The `MCPLogger` class automatically writes logs to the database when:
1. A database session is available in the context (`MCPLogger.set_db_session()`)
2. Log methods are called (`log_start`, `log_success`, `log_failed`, etc.)

### Context Variables

The logger uses Python context variables to track request context:

```python
# Set in request handler
MCPLogger.set_correlation_id()  # Auto-generated if not provided
MCPLogger.set_user_id(str(user.id))  # Optional
MCPLogger.set_source_id(str(source.id))  # Optional
MCPLogger.set_db_session(db)  # Required for database logging
```

These values are automatically included in database log entries.

### Fire-and-Forget

Database logging is **async and non-blocking**:
- Logs are written asynchronously using `asyncio.create_task()`
- Database errors don't affect application flow
- If database logging fails, logs still appear in console

## Usage Examples

### Example 1: Enable Database Logging for Search/Fetch

Currently, the search and fetch tools don't have database session context. To enable:

```python
@mcp.tool()
async def search(query: str, ctx: Context) -> Dict[str, List[Dict[str, Any]]]:
    # Set correlation ID
    correlation_id = MCPLogger.set_correlation_id()

    # Get database session and set in context
    async for db in get_db():
        MCPLogger.set_db_session(db)

        # Your search logic here
        # Logs will now be written to database
        timer_key = mcp_logger.log_start(MCPLogger.SEARCH, "aggregated_search", query=query)

        try:
            # ... perform search ...
            mcp_logger.log_success(MCPLogger.SEARCH, "aggregated_search", timer_key=timer_key)
        except Exception as e:
            mcp_logger.log_failed(MCPLogger.SEARCH, "aggregated_search", e, timer_key=timer_key)

        break  # Exit after first session
```

### Example 2: Query Logs from Database

```python
from repositories.log_repository import LogRepository
from database.config import get_db

async def get_user_search_history(user_id: str, limit: int = 100):
    async for db in get_db():
        log_repo = LogRepository(db)

        # Get all search operations for user
        logs = await log_repo.get_logs_by_user(
            user_id=uuid.UUID(user_id),
            operation="SEARCH",
            limit=limit
        )

        return logs
```

### Example 3: Trace a Request

```python
async def trace_request(correlation_id: str):
    async for db in get_db():
        log_repo = LogRepository(db)

        # Get all logs for this correlation ID (entire request flow)
        logs = await log_repo.get_logs_by_correlation_id(correlation_id)

        for log in logs:
            print(f"[{log.ts}] {log.method} | {log.status} | {log.text}")

        return logs
```

### Example 4: Get Operation Statistics

```python
async def get_user_stats(user_id: str):
    async for db in get_db():
        log_repo = LogRepository(db)

        # Get stats for last 24 hours
        stats = await log_repo.get_operation_stats(
            user_id=uuid.UUID(user_id),
            hours=24
        )

        print(f"Total operations: {stats['total_operations']}")
        print(f"Success rate: {stats['success_count']} / {stats['total_operations']}")
        print(f"Average time: {stats['avg_elapsed_sec']}s")
        print(f"By operation: {stats['by_operation']}")

        return stats
```

### Example 5: Clean Up Old Logs

```python
async def cleanup_old_logs(days: int = 30):
    async for db in get_db():
        log_repo = LogRepository(db)

        # Delete logs older than 30 days
        count = await log_repo.delete_old_logs(days=days)
        await db.commit()

        print(f"Deleted {count} old log entries")
        return count
```

## API Endpoints for Logs

You can create API endpoints to expose logs to users:

```python
# GET /api/v1/logs - Get user's logs
@mcp.custom_route("/api/v1/logs", methods=["GET"])
async def get_logs(request: Request):
    email, error_response = await get_current_user_from_request(request)
    if error_response:
        return error_response

    async for db in get_db():
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        if not user:
            return cors_error_response("User not found", 401, request)

        log_repo = LogRepository(db)

        # Parse query parameters
        limit = int(request.query_params.get("limit", 100))
        operation = request.query_params.get("operation", None)
        level = request.query_params.get("level", None)

        logs = await log_repo.get_logs_by_user(
            user_id=user.id,
            limit=limit,
            operation=operation,
            level=level
        )

        logs_data = []
        for log in logs:
            logs_data.append({
                "id": str(log.id),
                "text": log.text,
                "ts": log.ts,
                "level": log.level,
                "operation": log.operation,
                "method": log.method,
                "status": log.status,
                "correlation_id": log.correlation_id,
                "elapsed_sec": log.elapsed_sec,
                "metadata": log.metadata,
                "created_at": log.created_at.isoformat()
            })

        return cors_json_response(logs_data, 200, request)

# GET /api/v1/logs/stats - Get operation statistics
@mcp.custom_route("/api/v1/logs/stats", methods=["GET"])
async def get_log_stats(request: Request):
    email, error_response = await get_current_user_from_request(request)
    if error_response:
        return error_response

    async for db in get_db():
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        if not user:
            return cors_error_response("User not found", 401, request)

        log_repo = LogRepository(db)

        hours = int(request.query_params.get("hours", 24))
        stats = await log_repo.get_operation_stats(user_id=user.id, hours=hours)

        return cors_json_response(stats, 200, request)

# GET /api/v1/logs/trace/{correlation_id} - Trace a request
@mcp.custom_route("/api/v1/logs/trace/{correlation_id}", methods=["GET"])
async def trace_request(request: Request):
    email, error_response = await get_current_user_from_request(request)
    if error_response:
        return error_response

    correlation_id = request.path_params.get("correlation_id")

    async for db in get_db():
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        if not user:
            return cors_error_response("User not found", 401, request)

        log_repo = LogRepository(db)
        logs = await log_repo.get_logs_by_correlation_id(
            correlation_id=correlation_id,
            user_id=user.id
        )

        logs_data = []
        for log in logs:
            logs_data.append({
                "id": str(log.id),
                "text": log.text,
                "ts": log.ts,
                "level": log.level,
                "operation": log.operation,
                "method": log.method,
                "status": log.status,
                "elapsed_sec": log.elapsed_sec,
                "created_at": log.created_at.isoformat()
            })

        return cors_json_response(logs_data, 200, request)
```

## Performance Considerations

1. **Async Logging** - Database writes don't block request processing
2. **Indexed Queries** - All common query patterns are indexed
3. **Batch Cleanup** - Use `delete_old_logs()` periodically to prevent table bloat
4. **Metadata Storage** - Additional context stored as JSONB for flexible querying

## Log Retention

Recommended log retention policy:

- **Development**: 7 days
- **Production**: 30-90 days
- **Compliance**: As required by regulations

Use a cron job or scheduled task to run cleanup:

```bash
# Run daily cleanup (keep 30 days)
0 2 * * * cd /app && python -c "import asyncio; from main import cleanup_old_logs; asyncio.run(cleanup_old_logs(days=30))"
```

## Benefits

1. **Historical Analysis** - Query past operations and performance
2. **Debugging** - Trace requests across the entire system
3. **Monitoring** - Track success/failure rates and performance metrics
4. **Audit Trail** - Compliance and security auditing
5. **User Analytics** - Understand user behavior and usage patterns

## Notes

- User ID is nullable because some operations (health checks, public endpoints) don't have user context
- Source ID links logs to specific data sources when applicable
- The `text` field contains the full formatted log message for human readability
- Structured fields (`operation`, `status`, `elapsed_sec`) enable efficient querying
- Metadata field can store operation-specific details as JSON
