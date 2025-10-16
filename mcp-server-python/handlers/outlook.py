import logging
import os
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from .base import BaseHandler
from services.graph_client import GraphClient

load_dotenv()
logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

FOLDER_ALIASES = {
    "in:inbox": "inbox",
    "in:sent": "sentitems",
    "in:sentitems": "sentitems",
    "in:drafts": "drafts",
    "in:archive": "archive",
}

def _parse_query_for_graph(query: str):
    query = (query or "").strip()
    folder = "inbox"
    tokens: List[str] = []
    if query:
        for part in query.split():
            key = part.lower()
            if key in FOLDER_ALIASES:
                folder = FOLDER_ALIASES[key]
            else:
                tokens.append(part)
    rest = " ".join(tokens).strip()
    mode = "search" if rest else "filter"
    return {"folder": folder, "mode": mode, "filter": "", "search": rest}

class OutlookHandler(BaseHandler):
    name = "Outlook (Microsoft Graph)"
    id_prefix = "outlook"

    def __init__(self, tenant_id: str, client_id: str, client_secret: str, user_id: str, scope: str = "https://graph.microsoft.com/.default", graph_client: Optional[GraphClient] = None):
        super().__init__()
        self.user_id = user_id
        self.graph = graph_client or GraphClient(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope
        )

    # Implementations used by BaseHandler.search/fetch
    async def _search_impl(self, query: str, top: int = 10) -> List[Dict[str, Any]]:
        if not self.user_id:
            # Let the base class log the failure context; here just return empty
            return []

        q = _parse_query_for_graph(query)
        params = {
            "$top": str(top),
            "$select": "id,subject,from,receivedDateTime,isRead,webLink,bodyPreview",
        }
        path = f"/users/{self.user_id}/mailFolders/{q['folder']}/messages"
        consistency = False
        if q["mode"] == "search" and q["search"]:
            params["$search"] = f"\"{q['search']}\""
            consistency = True
        elif q["mode"] == "filter" and q["filter"]:
            params["$filter"] = q["filter"]

        data = await self.graph.get(path, params=params, consistency_eventual=consistency)
        results: List[Dict[str, Any]] = []
        for m in data.get("value", []):
            results.append(
                {
                    "id": f"{self.id_prefix}::{m['id']}",
                    "title": m.get("subject") or "(no subject)",
                    "text": self.make_snippet(m.get("bodyPreview") or "", 300),
                    "url": m.get("webLink") or None,
                }
            )
        return results

    async def _fetch_impl(self, native_id: str) -> Dict[str, Any]:
        if not self.user_id:
            raise RuntimeError("user_id is required to fetch Outlook messages")
        params = {"$select": "id,subject,from,receivedDateTime,isRead,webLink,body,bodyPreview"}
        msg = await self.graph.get(f"/users/{self.user_id}/messages/{native_id}", params=params)
        body = msg.get("body") or {}
        content = body.get("content") or msg.get("bodyPreview") or ""
        content_type = (body.get("contentType") or "").lower()
        return {
            "id": f"{self.id_prefix}::{msg['id']}",
            "title": msg.get("subject") or "(no subject)",
            "text": content,
            "url": msg.get("webLink") or None,
            "metadata": {
                "from": msg.get("from"),
                "receivedDateTime": msg.get("receivedDateTime"),
                "isRead": msg.get("isRead"),
                "contentType": content_type or None,
            },
        }
