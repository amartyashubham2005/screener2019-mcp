# base.py
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
import time

class BaseHandler(ABC):
    name: str
    id_prefix: str  # e.g., 'outlook'

    def __init__(self) -> None:
        # Per-class logger; override if you prefer module-level loggers
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    # ---------- Public API with shared logging ----------
    async def search(self, query: str, top: int = 10) -> List[Dict[str, Any]]:
        self.logger.info("[SEARCH] handler=%s query=%r top=%s", self.__class__.__name__, query, top)
        t0 = time.monotonic()
        try:
            results = await self._search_impl(query=query, top=top)
            self.logger.info(
                "[SEARCH] handler=%s results=%d elapsed=%.3fs",
                self.__class__.__name__, len(results), time.monotonic() - t0
            )
            return results
        except Exception:
            self.logger.exception("[SEARCH] handler=%s FAILED", self.__class__.__name__)
            raise

    async def fetch(self, native_id: str) -> Dict[str, Any]:
        self.logger.info("[FETCH] handler=%s id=%s", self.__class__.__name__, native_id)
        t0 = time.monotonic()
        try:
            obj = await self._fetch_impl(native_id=native_id)
            self.logger.info(
                "[FETCH] handler=%s ok elapsed=%.3fs",
                self.__class__.__name__, time.monotonic() - t0
            )
            return obj
        except Exception:
            self.logger.exception("[FETCH] handler=%s FAILED", self.__class__.__name__)
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
