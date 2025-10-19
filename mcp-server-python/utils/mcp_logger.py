"""
Structured logging utilities for MCP server operations.

This module provides a consistent logging convention across all MCP operations:
- Method invocation tracking
- Status transitions (START, IN_PROGRESS, SUCCESS, FAILED)
- Performance metrics (elapsed time, result counts)
- Request/Response tracking with correlation IDs
- Error details with stack traces

Log Format Convention:
  [MCP:{OPERATION}] {METHOD} | {STATUS} | {key=value pairs}

Example:
  [MCP:SEARCH] handler=OutlookHandler | START | query="project update" top=10 correlation_id=abc123
  [MCP:SEARCH] handler=OutlookHandler | SUCCESS | results=15 elapsed=1.234s correlation_id=abc123
"""

import logging
import time
import json
import traceback
from typing import Any, Dict, Optional, List
from contextvars import ContextVar
from datetime import datetime
import uuid

# Context variables for tracking request context across async operations
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
source_id_var: ContextVar[Optional[str]] = ContextVar('source_id', default=None)
db_session_var: ContextVar[Optional[Any]] = ContextVar('db_session', default=None)

class MCPLogger:
    """
    Structured logger for MCP operations with consistent formatting and metrics.
    """

    # Operation types
    SEARCH = "SEARCH"
    FETCH = "FETCH"
    AUTH = "AUTH"
    CRUD = "CRUD"
    HEALTH = "HEALTH"
    HANDLER_INIT = "HANDLER_INIT"
    DB_QUERY = "DB_QUERY"
    API_CALL = "API_CALL"

    # Status types
    START = "START"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    WARNING = "WARNING"

    def __init__(self, name: str):
        """
        Initialize logger for a specific module/class.

        Args:
            name: Logger name (typically module.ClassName)
        """
        self.logger = logging.getLogger(name)
        self.operation_timers: Dict[str, float] = {}

    @staticmethod
    def set_correlation_id(correlation_id: Optional[str] = None) -> str:
        """
        Set correlation ID for current request context.

        Args:
            correlation_id: Optional correlation ID. If None, generates a new UUID.

        Returns:
            The correlation ID that was set
        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())[:8]
        correlation_id_var.set(correlation_id)
        return correlation_id

    @staticmethod
    def get_correlation_id() -> str:
        """Get current correlation ID from context."""
        return correlation_id_var.get() or "unknown"

    @staticmethod
    def set_user_id(user_id: Optional[str]) -> None:
        """Set user ID for current request context."""
        user_id_var.set(user_id)

    @staticmethod
    def get_user_id() -> Optional[str]:
        """Get current user ID from context."""
        return user_id_var.get()

    @staticmethod
    def set_source_id(source_id: Optional[str]) -> None:
        """Set source ID for current request context."""
        source_id_var.set(source_id)

    @staticmethod
    def get_source_id() -> Optional[str]:
        """Get current source ID from context."""
        return source_id_var.get()

    @staticmethod
    def set_db_session(db_session: Any) -> None:
        """Set database session for current request context."""
        db_session_var.set(db_session)

    @staticmethod
    def get_db_session() -> Optional[Any]:
        """Get current database session from context."""
        return db_session_var.get()

    def _format_log_message(
        self,
        operation: str,
        method: str,
        status: str,
        **kwargs
    ) -> str:
        """
        Format log message according to MCP convention.

        Args:
            operation: Operation type (SEARCH, FETCH, etc.)
            method: Method/handler name
            status: Status (START, SUCCESS, FAILED, etc.)
            **kwargs: Additional key-value pairs to log

        Returns:
            Formatted log message string
        """
        # Add correlation ID if available
        correlation_id = self.get_correlation_id()
        if correlation_id and correlation_id != "unknown":
            kwargs['correlation_id'] = correlation_id

        # Format key-value pairs
        kv_parts = []
        for key, value in kwargs.items():
            if value is None:
                continue
            # Format based on type
            if isinstance(value, (int, float, bool)):
                kv_parts.append(f"{key}={value}")
            elif isinstance(value, str):
                # Quote strings with spaces
                if ' ' in value or not value:
                    kv_parts.append(f'{key}="{value}"')
                else:
                    kv_parts.append(f"{key}={value}")
            elif isinstance(value, (list, dict)):
                # JSON encode complex types
                kv_parts.append(f"{key}={json.dumps(value)}")
            else:
                kv_parts.append(f"{key}={str(value)}")

        kv_str = " ".join(kv_parts) if kv_parts else ""
        return f"[MCP:{operation}] {method} | {status} | {kv_str}"

    async def _write_to_database(
        self,
        text: str,
        level: str,
        operation: Optional[str] = None,
        method: Optional[str] = None,
        status: Optional[str] = None,
        elapsed_sec: Optional[float] = None,
        **metadata
    ) -> None:
        """
        Write log entry to database if session is available.

        Args:
            text: Log message text
            level: Log level (INFO, WARNING, ERROR)
            operation: Operation type
            method: Method name
            status: Status type
            elapsed_sec: Elapsed time in seconds
            **metadata: Additional metadata to store
        """
        try:
            db_session = self.get_db_session()
            if not db_session:
                return

            # Import here to avoid circular dependency
            from repositories.log_repository import LogRepository

            log_repo = LogRepository(db_session)

            # Get user and source from context
            user_id_str = self.get_user_id()
            source_id_str = self.get_source_id()
            correlation_id = self.get_correlation_id()

            # Convert string IDs to UUID if present
            user_id = uuid.UUID(user_id_str) if user_id_str else None
            source_id = uuid.UUID(source_id_str) if source_id_str else None

            # Create log entry
            await log_repo.create_log(
                text=text,
                level=level,
                ts=int(time.time() * 1000),  # Current time in epoch milliseconds
                user_id=user_id,
                source_id=source_id,
                operation=operation,
                method=method,
                status=status,
                correlation_id=correlation_id if correlation_id != "unknown" else None,
                elapsed_sec=elapsed_sec,
                metadata=metadata if metadata else None
            )

            # Commit the log entry
            await db_session.commit()

        except Exception as e:
            # Don't let database logging errors break the application
            # Just log to console
            self.logger.warning(f"Failed to write log to database: {e}")

    def log_start(
        self,
        operation: str,
        method: str,
        **kwargs
    ) -> str:
        """
        Log the start of an operation and start a timer.

        Args:
            operation: Operation type
            method: Method/handler name
            **kwargs: Additional context (query, id, params, etc.)

        Returns:
            Timer key for use with log_end
        """
        timer_key = f"{operation}:{method}:{self.get_correlation_id()}"
        self.operation_timers[timer_key] = time.monotonic()

        message = self._format_log_message(operation, method, self.START, **kwargs)
        self.logger.info(message)

        # Write to database asynchronously (fire and forget)
        try:
            import asyncio
            asyncio.create_task(
                self._write_to_database(
                    text=message,
                    level="INFO",
                    operation=operation,
                    method=method,
                    status=self.START,
                    **kwargs
                )
            )
        except Exception:
            pass  # Ignore database logging errors

        return timer_key

    def log_progress(
        self,
        operation: str,
        method: str,
        **kwargs
    ) -> None:
        """
        Log progress update during an operation.

        Args:
            operation: Operation type
            method: Method/handler name
            **kwargs: Progress details (items_processed, current_step, etc.)
        """
        message = self._format_log_message(operation, method, self.IN_PROGRESS, **kwargs)
        self.logger.info(message)

    def log_success(
        self,
        operation: str,
        method: str,
        timer_key: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log successful completion of an operation.

        Args:
            operation: Operation type
            method: Method/handler name
            timer_key: Optional timer key from log_start to calculate elapsed time
            **kwargs: Result details (results_count, status_code, etc.)
        """
        # Calculate elapsed time if timer exists
        elapsed_sec = None
        if timer_key and timer_key in self.operation_timers:
            elapsed = time.monotonic() - self.operation_timers[timer_key]
            elapsed_sec = round(elapsed, 3)
            kwargs['elapsed_sec'] = elapsed_sec
            del self.operation_timers[timer_key]

        message = self._format_log_message(operation, method, self.SUCCESS, **kwargs)
        self.logger.info(message)

        # Write to database asynchronously (fire and forget)
        try:
            import asyncio
            asyncio.create_task(
                self._write_to_database(
                    text=message,
                    level="INFO",
                    operation=operation,
                    method=method,
                    status=self.SUCCESS,
                    elapsed_sec=elapsed_sec,
                    **kwargs
                )
            )
        except Exception:
            pass  # Ignore database logging errors

    def log_failed(
        self,
        operation: str,
        method: str,
        error: Exception,
        timer_key: Optional[str] = None,
        include_trace: bool = True,
        **kwargs
    ) -> None:
        """
        Log failed operation with error details.

        Args:
            operation: Operation type
            method: Method/handler name
            error: Exception that caused the failure
            timer_key: Optional timer key from log_start
            include_trace: Whether to include full stack trace
            **kwargs: Additional error context
        """
        # Calculate elapsed time if timer exists
        elapsed_sec = None
        if timer_key and timer_key in self.operation_timers:
            elapsed = time.monotonic() - self.operation_timers[timer_key]
            elapsed_sec = round(elapsed, 3)
            kwargs['elapsed_sec'] = elapsed_sec
            del self.operation_timers[timer_key]

        # Add error details
        kwargs['error_type'] = type(error).__name__
        kwargs['error_message'] = str(error)

        message = self._format_log_message(operation, method, self.FAILED, **kwargs)

        if include_trace:
            # Log with full exception traceback
            self.logger.error(message, exc_info=True)
        else:
            self.logger.error(message)

        # Write to database asynchronously (fire and forget)
        try:
            import asyncio
            asyncio.create_task(
                self._write_to_database(
                    text=message,
                    level="ERROR",
                    operation=operation,
                    method=method,
                    status=self.FAILED,
                    elapsed_sec=elapsed_sec,
                    **kwargs
                )
            )
        except Exception:
            pass  # Ignore database logging errors

    def log_warning(
        self,
        operation: str,
        method: str,
        warning_message: str,
        **kwargs
    ) -> None:
        """
        Log a warning during an operation.

        Args:
            operation: Operation type
            method: Method/handler name
            warning_message: Warning description
            **kwargs: Additional warning context
        """
        kwargs['warning'] = warning_message
        message = self._format_log_message(operation, method, self.WARNING, **kwargs)
        self.logger.warning(message)

    # Convenience methods for common operations

    def search_start(self, handler: str, query: str, top: int = 10, **kwargs) -> str:
        """Log start of search operation."""
        return self.log_start(self.SEARCH, handler, query=query, top=top, **kwargs)

    def search_success(self, handler: str, results_count: int, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log successful search completion."""
        self.log_success(self.SEARCH, handler, timer_key, results_count=results_count, **kwargs)

    def search_failed(self, handler: str, error: Exception, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log failed search."""
        self.log_failed(self.SEARCH, handler, error, timer_key, **kwargs)

    def fetch_start(self, handler: str, native_id: str, **kwargs) -> str:
        """Log start of fetch operation."""
        return self.log_start(self.FETCH, handler, native_id=native_id, **kwargs)

    def fetch_success(self, handler: str, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log successful fetch completion."""
        self.log_success(self.FETCH, handler, timer_key, **kwargs)

    def fetch_failed(self, handler: str, error: Exception, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log failed fetch."""
        self.log_failed(self.FETCH, handler, error, timer_key, **kwargs)

    def auth_start(self, method: str, email: Optional[str] = None, **kwargs) -> str:
        """Log start of auth operation."""
        if email:
            kwargs['email'] = email
        return self.log_start(self.AUTH, method, **kwargs)

    def auth_success(self, method: str, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log successful auth operation."""
        self.log_success(self.AUTH, method, timer_key, **kwargs)

    def auth_failed(self, method: str, error: Exception, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log failed auth operation."""
        self.log_failed(self.AUTH, method, error, timer_key, include_trace=False, **kwargs)

    def crud_start(self, operation: str, entity: str, entity_id: Optional[str] = None, **kwargs) -> str:
        """Log start of CRUD operation (create/read/update/delete)."""
        if entity_id:
            kwargs['entity_id'] = entity_id
        return self.log_start(self.CRUD, f"{operation}_{entity}", **kwargs)

    def crud_success(self, operation: str, entity: str, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log successful CRUD operation."""
        self.log_success(self.CRUD, f"{operation}_{entity}", timer_key, **kwargs)

    def crud_failed(self, operation: str, entity: str, error: Exception, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log failed CRUD operation."""
        self.log_failed(self.CRUD, f"{operation}_{entity}", error, timer_key, **kwargs)

    def db_query_start(self, query_type: str, **kwargs) -> str:
        """Log start of database query."""
        return self.log_start(self.DB_QUERY, query_type, **kwargs)

    def db_query_success(self, query_type: str, rows_affected: Optional[int] = None, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log successful database query."""
        if rows_affected is not None:
            kwargs['rows_affected'] = rows_affected
        self.log_success(self.DB_QUERY, query_type, timer_key, **kwargs)

    def db_query_failed(self, query_type: str, error: Exception, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log failed database query."""
        self.log_failed(self.DB_QUERY, query_type, error, timer_key, **kwargs)

    def api_call_start(self, api: str, endpoint: str, method: str = "GET", **kwargs) -> str:
        """Log start of external API call."""
        return self.log_start(self.API_CALL, f"{api}.{endpoint}", http_method=method, **kwargs)

    def api_call_success(self, api: str, endpoint: str, status_code: int, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log successful API call."""
        self.log_success(self.API_CALL, f"{api}.{endpoint}", timer_key, status_code=status_code, **kwargs)

    def api_call_failed(self, api: str, endpoint: str, error: Exception, timer_key: Optional[str] = None, **kwargs) -> None:
        """Log failed API call."""
        self.log_failed(self.API_CALL, f"{api}.{endpoint}", error, timer_key, **kwargs)


# Global logger factory
def get_mcp_logger(name: str) -> MCPLogger:
    """
    Get or create an MCPLogger instance for a module/class.

    Args:
        name: Logger name (typically __name__ or f"{__name__}.{ClassName}")

    Returns:
        MCPLogger instance
    """
    return MCPLogger(name)


# Configure root MCP logging format
def configure_mcp_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    include_timestamp: bool = True
) -> None:
    """
    Configure MCP logging with consistent formatting.

    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string (default: timestamp + level + message)
        include_timestamp: Whether to include timestamp in logs
    """
    if format_string is None:
        if include_timestamp:
            format_string = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        else:
            format_string = '%(levelname)-8s | %(name)s | %(message)s'

    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
