# base.py
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
import time
from utils.mcp_logger import get_mcp_logger

class BaseHandler(ABC):
    name: str
    id_prefix: str  # e.g., 'outlook'

    def __init__(self) -> None:
        # Use structured MCP logger
        self.mcp_logger = get_mcp_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        # Keep legacy logger for backwards compatibility
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    # ---------- Public API with shared logging ----------
    async def search(self, query: str, top: int = 10) -> List[Dict[str, Any]]:
        """
        Execute search operation with structured logging.

        Args:
            query: Search query string
            top: Maximum number of results to return

        Returns:
            List of search results
        """
        handler_name = self.__class__.__name__
        timer_key = self.mcp_logger.search_start(handler_name, query, top)

        try:
            results = await self._search_impl(query=query, top=top)
            self.mcp_logger.search_success(
                handler_name,
                results_count=len(results),
                timer_key=timer_key
            )
            return results
        except Exception as e:
            self.mcp_logger.search_failed(handler_name, e, timer_key=timer_key)
            raise

    async def fetch(self, native_id: str) -> Dict[str, Any]:
        """
        Execute fetch operation with structured logging.

        Args:
            native_id: Native identifier for the resource

        Returns:
            Dict containing the fetched resource
        """
        handler_name = self.__class__.__name__
        timer_key = self.mcp_logger.fetch_start(handler_name, native_id)

        try:
            obj = await self._fetch_impl(native_id=native_id)
            self.mcp_logger.fetch_success(handler_name, timer_key=timer_key)
            return obj
        except Exception as e:
            self.mcp_logger.fetch_failed(handler_name, e, timer_key=timer_key)
            raise

    # ---------- Implementation hooks for subclasses ----------
    @abstractmethod
    async def _search_impl(self, query: str, top: int = 10) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def _fetch_impl(self, native_id: str) -> Dict[str, Any]:
        ...

    # Optional: shared helpers for all handlers can live here
    @staticmethod
    def make_snippet(text: Optional[str], max_len: int = 200) -> str:
        text = (text or "").strip()
        return (text[:max_len] + "...") if len(text) > max_len else text
