# MCP Server Logging Convention

This document describes the structured logging system used across the MCP server for consistent, traceable, and informative logs.

## Log Format

All MCP operations follow this structured format:

```
TIMESTAMP | LEVEL | MODULE | [MCP:OPERATION] METHOD | STATUS | key=value pairs
```

### Example Logs

```
2025-10-19 12:34:56 | INFO | main | [MCP:SEARCH] aggregated_search | START | query="project update" domain=localhost:8000 correlation_id=a1b2c3d4
2025-10-19 12:34:56 | INFO | main | [MCP:SEARCH] aggregated_search | IN_PROGRESS | handlers_loaded=3 box=1 snowflake=1 outlook=1 correlation_id=a1b2c3d4
2025-10-19 12:34:56 | INFO | handlers.outlook.OutlookHandler | [MCP:SEARCH] OutlookHandler | START | query="project update" top=10 correlation_id=a1b2c3d4
2025-10-19 12:34:57 | INFO | handlers.outlook.OutlookHandler | [MCP:SEARCH] OutlookHandler | SUCCESS | results_count=15 elapsed_sec=0.892 correlation_id=a1b2c3d4
2025-10-19 12:34:57 | INFO | main | [MCP:SEARCH] aggregated_search | SUCCESS | total_results=28 handlers_succeeded=3 handlers_failed=0 elapsed_sec=1.234 correlation_id=a1b2c3d4
```

## Components

### 1. Operation Types

| Operation | Description | Used For |
|-----------|-------------|----------|
| `SEARCH` | Search operations across handlers | `search()` tool |
| `FETCH` | Fetching specific resources | `fetch()` tool |
| `AUTH` | Authentication operations | signup, signin, signout |
| `CRUD` | CRUD operations on sources/servers | Create, Read, Update, Delete |
| `HEALTH` | Health check operations | `/api/v1/checks` |
| `HANDLER_INIT` | Handler initialization | Dynamic handler loading |
| `DB_QUERY` | Database queries | Repository operations |
| `API_CALL` | External API calls | Graph API, Snowflake API, etc. |

### 2. Status Types

| Status | Description | When Used |
|--------|-------------|-----------|
| `START` | Operation beginning | Start of any operation |
| `IN_PROGRESS` | Operation in progress | Intermediate steps |
| `SUCCESS` | Operation completed successfully | Successful completion |
| `FAILED` | Operation failed | On exception/error |
| `WARNING` | Non-fatal issue | Degraded operation |

### 3. Correlation IDs

Each request is assigned a unique **correlation ID** that tracks it across:
- Main aggregation function
- Individual handlers
- Database queries
- External API calls

This allows you to trace a single request through the entire system.

**Example:** Find all logs for request `a1b2c3d4`:
```bash
grep "correlation_id=a1b2c3d4" logs.txt
```

### 4. Tracked Metrics

All operations automatically track:

| Metric | Description | Example |
|--------|-------------|---------|
| `elapsed_sec` | Time taken in seconds | `elapsed_sec=1.234` |
| `results_count` | Number of results returned | `results_count=15` |
| `handlers_loaded` | Number of handlers initialized | `handlers_loaded=3` |
| `handlers_succeeded` | Number of successful handlers | `handlers_succeeded=2` |
| `handlers_failed` | Number of failed handlers | `handlers_failed=1` |
| `error_type` | Exception class name | `error_type=ConnectionError` |
| `error_message` | Error description | `error_message="Connection timeout"` |

## Usage Examples

### Example 1: Search Operation Flow

```
# Request starts
[MCP:SEARCH] aggregated_search | START | query="sales data" correlation_id=abc123

# Load handlers
[MCP:SEARCH] aggregated_search | IN_PROGRESS | handlers_loaded=3 box=1 snowflake=1 outlook=1

# Each handler executes
[MCP:SEARCH] SnowflakeHandler | START | query="sales data" top=10 correlation_id=abc123
[MCP:SEARCH] SnowflakeHandler | SUCCESS | results_count=5 elapsed_sec=0.456

[MCP:SEARCH] OutlookHandler | START | query="sales data" top=10 correlation_id=abc123
[MCP:SEARCH] OutlookHandler | FAILED | error_type=AuthenticationError error_message="Token expired" elapsed_sec=0.123

# Aggregate completes
[MCP:SEARCH] aggregated_search | SUCCESS | total_results=5 handlers_succeeded=2 handlers_failed=1 elapsed_sec=0.678
```

### Example 2: Fetch Operation Flow

```
# Request starts
[MCP:FETCH] aggregated_fetch | START | id=outlook::AAMkAGI2... prefix=outlook correlation_id=def456

# Progress update
[MCP:FETCH] aggregated_fetch | IN_PROGRESS | available_prefixes=["outlook","snowflake","box"] handlers_loaded=3

# Handler executes
[MCP:FETCH] OutlookHandler | START | native_id=AAMkAGI2... correlation_id=def456
[MCP:FETCH] OutlookHandler | SUCCESS | elapsed_sec=0.234

# Fetch completes
[MCP:FETCH] aggregated_fetch | SUCCESS | handler=OutlookHandler prefix=outlook elapsed_sec=0.345
```

### Example 3: Authentication Flow

```
[MCP:AUTH] signin | START | email=user@example.com
[MCP:AUTH] signin | SUCCESS | user_id=550e8400-e29b-41d4-a716-446655440000 elapsed_sec=0.123
```

### Example 4: CRUD Operation Flow

```
[MCP:CRUD] create_source | START | user_id=550e8400... type=outlook
[MCP:CRUD] create_source | SUCCESS | source_id=440e8400... elapsed_sec=0.089
```

### Example 5: Failed Operation with Error

```
[MCP:SEARCH] SnowflakeHandler | START | query="invalid query" correlation_id=ghi789
[MCP:SEARCH] SnowflakeHandler | FAILED | error_type=SQLExecutionError error_message="Invalid SQL syntax" elapsed_sec=0.045 correlation_id=ghi789
Traceback (most recent call last):
  File "handlers/snowflake_cortex.py", line 45, in _search_impl
    results = await self.client.query(sql)
SQLExecutionError: Invalid SQL syntax near 'invalid'
```

## Filtering and Analysis

### Find all failed operations
```bash
grep "FAILED" logs.txt
```

### Find slow operations (>1 second)
```bash
grep -E "elapsed_sec=[1-9][0-9]*\." logs.txt
```

### Trace a specific request
```bash
grep "correlation_id=abc123" logs.txt
```

### Find operations by handler
```bash
grep "OutlookHandler" logs.txt
```

### Find all search operations
```bash
grep "\[MCP:SEARCH\]" logs.txt
```

### Count operations by status
```bash
grep -c "| SUCCESS |" logs.txt
grep -c "| FAILED |" logs.txt
```

## Adding Logging to New Code

### Example 1: Add logging to a new handler

```python
from utils.mcp_logger import get_mcp_logger

class MyNewHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        # MCP logger is automatically available via self.mcp_logger

    async def _search_impl(self, query: str, top: int = 10):
        # Logging is automatic via BaseHandler.search()
        # Just implement your logic
        results = await self.my_api.search(query, limit=top)
        return results
```

### Example 2: Add logging to a new API endpoint

```python
from utils.mcp_logger import get_mcp_logger, MCPLogger

mcp_logger = get_mcp_logger(__name__)

@mcp.custom_route("/api/v1/my-endpoint", methods=["POST"])
async def my_endpoint(request: Request):
    # Set correlation ID
    correlation_id = MCPLogger.set_correlation_id()

    # Start timer
    timer_key = mcp_logger.log_start(
        MCPLogger.CRUD,
        "my_endpoint",
        user_id=user.id,
        correlation_id=correlation_id
    )

    try:
        # Your logic here
        result = await do_something()

        # Log success
        mcp_logger.log_success(
            MCPLogger.CRUD,
            "my_endpoint",
            timer_key=timer_key,
            result_count=len(result)
        )

        return cors_json_response(result)

    except Exception as e:
        # Log failure
        mcp_logger.log_failed(
            MCPLogger.CRUD,
            "my_endpoint",
            e,
            timer_key=timer_key
        )
        raise
```

### Example 3: Add logging to database operations

```python
from utils.mcp_logger import get_mcp_logger, MCPLogger

class MyRepository:
    def __init__(self, db):
        self.db = db
        self.mcp_logger = get_mcp_logger(__name__)

    async def get_items(self, user_id: str):
        timer_key = self.mcp_logger.db_query_start(
            "get_items",
            user_id=user_id
        )

        try:
            result = await self.db.execute(query)
            rows = result.fetchall()

            self.mcp_logger.db_query_success(
                "get_items",
                rows_affected=len(rows),
                timer_key=timer_key
            )

            return rows

        except Exception as e:
            self.mcp_logger.db_query_failed(
                "get_items",
                e,
                timer_key=timer_key
            )
            raise
```

## Configuration

Configure logging in `main.py`:

```python
from utils.mcp_logger import configure_mcp_logging

# Configure with timestamps
configure_mcp_logging(
    level=logging.INFO,
    include_timestamp=True
)

# Or configure with custom format
configure_mcp_logging(
    level=logging.DEBUG,
    format_string='%(asctime)s | %(levelname)s | %(message)s',
    include_timestamp=True
)
```

## Best Practices

1. **Always set correlation ID** at the start of request handlers
2. **Use timer_key** to automatically track elapsed time
3. **Log intermediate progress** for long-running operations
4. **Include relevant context** in key-value pairs (user_id, query, etc.)
5. **Don't log sensitive data** (passwords, tokens, full auth headers)
6. **Use appropriate log levels**:
   - `INFO`: Normal operations (START, SUCCESS, IN_PROGRESS)
   - `WARNING`: Degraded operations (partial failures)
   - `ERROR`: Failed operations (FAILED status)
7. **Set include_trace=False** for expected errors (validation, auth failures)

## Performance Impact

The structured logging system is designed to be lightweight:
- Correlation IDs use context vars (no global state)
- Timers use `time.monotonic()` (high precision, low overhead)
- String formatting is deferred until actually logged
- No significant performance impact on typical operations

## Troubleshooting

### Logs are too verbose
Increase log level:
```python
configure_mcp_logging(level=logging.WARNING)
```

### Missing correlation IDs
Ensure `MCPLogger.set_correlation_id()` is called at request entry:
```python
correlation_id = MCPLogger.set_correlation_id()
```

### Logs not showing
Check that logging is configured before creating loggers:
```python
# MUST be before get_mcp_logger() calls
configure_mcp_logging()
```

### Timer not working
Ensure you're passing the timer_key to log_success/log_failed:
```python
timer_key = logger.log_start(...)
logger.log_success(..., timer_key=timer_key)
```
