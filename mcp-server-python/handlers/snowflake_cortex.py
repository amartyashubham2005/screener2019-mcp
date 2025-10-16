import hashlib
import json
import logging
import os
import re
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from .base import BaseHandler
from services.snowflake_cortex_client import SnowflakeCortexClient

load_dotenv()
logger = logging.getLogger(__name__)

URI_PREFIX = "sfc://"
# =============== Small in-memory caches =================
@dataclass
class CacheEntry:
    at: float
    ttl: float
    value: Any


class TinyCache:
    def __init__(self):
        self._m: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        e = self._m.get(key)
        if not e:
            return None
        if (time.time() - e.at) > e.ttl:
            self._m.pop(key, None)
            return None
        return e.value

    def set(self, key: str, value: Any, ttl: float = 120.0):
        self._m[key] = CacheEntry(at=time.time(), ttl=ttl, value=value)

# =============== Handler =================
class SnowflakeCortexHandler(BaseHandler):
    name = "Snowflake Cortex (REST SQL API, URI model)"
    id_prefix = "snowflake_cortex"  # for MCP routing ("snowflake::<native_id>")

    def __init__(self, semantic_model_file: str, cortex_search_service: str, snowflake_account_url: str, snowflake_pat: str, client: Optional[SnowflakeCortexClient] = None):
        super().__init__()
        self.sf = client or SnowflakeCortexClient(
            semantic_model_file=semantic_model_file,
            cortex_search_service=cortex_search_service,
            snowflake_account_url=snowflake_account_url,
            snowflake_pat=snowflake_pat
        )

    # ------------- SEARCH -------------
    async def _search_impl(self, query: str, top: int = 25) -> List[Dict[str, Any]]:
        # retval = [{
        #     "id": json.dumps(await self.sf.run_cortex_agents(query))
        # }]
        retval = [{
            "id": f"{self.id_prefix}::{query}",
            "metadata": await self.sf.run_cortex_agents(query)
        }]
        print('retval _search_impl', retval)
        return retval

    # ------------- FETCH -------------
    async def _fetch_impl(self, native_id: str) -> Dict[str, Any]:
       # TODO: Implement
       retval = await self.sf.run_cortex_agents(native_id)
       print('retval _fetch_impl', retval)
       return retval
   