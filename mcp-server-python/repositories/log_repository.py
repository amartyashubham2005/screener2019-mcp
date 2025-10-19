"""
Repository for Log database operations.
"""

import uuid
import time
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Log


class LogRepository:
    """Repository for managing logs in the database."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        text: str,
        level: str,
        ts: Optional[int] = None,
        user_id: Optional[uuid.UUID] = None,
        source_id: Optional[uuid.UUID] = None,
        operation: Optional[str] = None,
        method: Optional[str] = None,
        status: Optional[str] = None,
        correlation_id: Optional[str] = None,
        elapsed_sec: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Log:
        """
        Create a new log entry.

        Args:
            text: Log message text
            level: Log level (INFO, WARNING, ERROR, etc.)
            ts: Timestamp in epoch milliseconds (defaults to current time)
            user_id: Optional user ID
            source_id: Optional source ID
            operation: Optional operation type (SEARCH, FETCH, etc.)
            method: Optional method name
            status: Optional status (START, SUCCESS, FAILED, etc.)
            correlation_id: Optional correlation ID
            elapsed_sec: Optional elapsed time in seconds
            metadata: Optional additional metadata as JSON

        Returns:
            Created Log instance
        """
        if ts is None:
            ts = int(time.time() * 1000)  # Current time in epoch milliseconds

        log = Log(
            text=text,
            level=level,
            ts=ts,
            user_id=user_id,
            source_id=source_id,
            operation=operation,
            method=method,
            status=status,
            correlation_id=correlation_id,
            elapsed_sec=elapsed_sec,
            log_metadata=metadata
        )

        self.db.add(log)
        # Note: Caller should commit explicitly
        return log

    async def get_logs_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
        operation: Optional[str] = None,
        level: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[Log]:
        """
        Get logs for a specific user with optional filters.

        Args:
            user_id: User ID to filter by
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            operation: Optional operation type filter
            level: Optional log level filter
            correlation_id: Optional correlation ID filter

        Returns:
            List of Log instances
        """
        query = select(Log).where(Log.user_id == user_id)

        if operation:
            query = query.where(Log.operation == operation)
        if level:
            query = query.where(Log.level == level)
        if correlation_id:
            query = query.where(Log.correlation_id == correlation_id)

        query = query.order_by(desc(Log.ts)).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_logs_by_source(
        self,
        source_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Log]:
        """
        Get logs for a specific source.

        Args:
            source_id: Source ID to filter by
            limit: Maximum number of logs to return
            offset: Number of logs to skip

        Returns:
            List of Log instances
        """
        query = select(Log).where(
            Log.source_id == source_id
        ).order_by(desc(Log.ts)).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_logs_by_correlation_id(
        self,
        correlation_id: str,
        user_id: Optional[uuid.UUID] = None
    ) -> List[Log]:
        """
        Get all logs for a specific correlation ID (to trace a single request).

        Args:
            correlation_id: Correlation ID to filter by
            user_id: Optional user ID filter

        Returns:
            List of Log instances ordered by timestamp
        """
        query = select(Log).where(Log.correlation_id == correlation_id)

        if user_id:
            query = query.where(Log.user_id == user_id)

        query = query.order_by(Log.ts)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_logs_by_time_range(
        self,
        start_ts: int,
        end_ts: int,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 1000
    ) -> List[Log]:
        """
        Get logs within a specific time range.

        Args:
            start_ts: Start timestamp in epoch milliseconds
            end_ts: End timestamp in epoch milliseconds
            user_id: Optional user ID filter
            limit: Maximum number of logs to return

        Returns:
            List of Log instances
        """
        query = select(Log).where(
            and_(
                Log.ts >= start_ts,
                Log.ts <= end_ts
            )
        )

        if user_id:
            query = query.where(Log.user_id == user_id)

        query = query.order_by(desc(Log.ts)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_failed_operations(
        self,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        hours: int = 24
    ) -> List[Log]:
        """
        Get recent failed operations.

        Args:
            user_id: Optional user ID filter
            limit: Maximum number of logs to return
            hours: Number of hours to look back (default: 24)

        Returns:
            List of failed Log instances
        """
        cutoff_ts = int((time.time() - (hours * 3600)) * 1000)

        query = select(Log).where(
            and_(
                Log.status == "FAILED",
                Log.ts >= cutoff_ts
            )
        )

        if user_id:
            query = query.where(Log.user_id == user_id)

        query = query.order_by(desc(Log.ts)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_old_logs(
        self,
        days: int = 30,
        user_id: Optional[uuid.UUID] = None
    ) -> int:
        """
        Delete logs older than specified days.

        Args:
            days: Number of days to retain (logs older than this will be deleted)
            user_id: Optional user ID filter (if provided, only delete that user's logs)

        Returns:
            Number of logs deleted
        """
        cutoff_ts = int((time.time() - (days * 86400)) * 1000)

        query = select(Log).where(Log.ts < cutoff_ts)

        if user_id:
            query = query.where(Log.user_id == user_id)

        result = await self.db.execute(query)
        logs_to_delete = result.scalars().all()

        count = len(logs_to_delete)
        for log in logs_to_delete:
            await self.db.delete(log)

        # Note: Caller should commit explicitly
        return count

    async def get_operation_stats(
        self,
        user_id: uuid.UUID,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get operation statistics for a user over the last N hours.

        Args:
            user_id: User ID
            hours: Number of hours to look back

        Returns:
            Dictionary with operation statistics
        """
        cutoff_ts = int((time.time() - (hours * 3600)) * 1000)

        query = select(Log).where(
            and_(
                Log.user_id == user_id,
                Log.ts >= cutoff_ts,
                Log.operation.isnot(None)
            )
        )

        result = await self.db.execute(query)
        logs = result.scalars().all()

        stats = {
            "total_operations": len(logs),
            "by_operation": {},
            "by_status": {},
            "failed_count": 0,
            "success_count": 0,
            "avg_elapsed_sec": 0.0
        }

        elapsed_times = []

        for log in logs:
            # Count by operation
            if log.operation:
                if log.operation not in stats["by_operation"]:
                    stats["by_operation"][log.operation] = 0
                stats["by_operation"][log.operation] += 1

            # Count by status
            if log.status:
                if log.status not in stats["by_status"]:
                    stats["by_status"][log.status] = 0
                stats["by_status"][log.status] += 1

                if log.status == "FAILED":
                    stats["failed_count"] += 1
                elif log.status == "SUCCESS":
                    stats["success_count"] += 1

            # Track elapsed times
            if log.elapsed_sec is not None:
                elapsed_times.append(log.elapsed_sec)

        if elapsed_times:
            stats["avg_elapsed_sec"] = round(sum(elapsed_times) / len(elapsed_times), 3)

        return stats
