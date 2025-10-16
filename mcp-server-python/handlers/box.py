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
from services.box_client import BoxClient

load_dotenv()
logger = logging.getLogger(__name__)

URI_PREFIX = "box://"

# =============== Handler =================
class BoxHandler(BaseHandler):
    name = "Box (REST SQL API, URI model)"
    id_prefix = "box"  # for MCP routing ("box::<native_id>")

    def __init__(self, client_id: str, client_secret: str, subject_type: str, subject_id: str, client: Optional[BoxClient] = None):
        super().__init__()
        self.sf = client or BoxClient(
            client_id=client_id,
            client_secret=client_secret,
            subject_type=subject_type,
            subject_id=subject_id
        )

    # ------------- SEARCH -------------
    async def _search_impl(self, query: str, top: int = 25) -> List[Dict[str, Any]]:
        retval = [{
            "id": f"{self.id_prefix}::{query}",
            # TODO: return title and url
            # "title": "Microsoft 20254annual report",
            # "url": "https://view.officeapps.live.com/op/view.aspx?src=https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/MSFT_FY24Q4_10K"
            "metadata": await self.sf.run_box_agents(query)
        }]
        print('retval _search_impl', retval)
        return retval

    # ------------- FETCH -------------
    async def _fetch_impl(self, native_id: str) -> Dict[str, Any]:
       # TODO: Implement
       retval = await self.sf.run_box_agents(native_id)
       print('retval _fetch_impl', retval)
       return retval
   