import logging
import os
import time
from typing import Optional, Dict

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

class GraphClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, scope: str = "https://graph.microsoft.com/.default", base_url: str = GRAPH_BASE):
        if not tenant_id:
            raise RuntimeError("tenant_id is required")
        if not client_id:
            raise RuntimeError("client_id is required")
        if not client_secret:
            raise RuntimeError("client_secret is required")
            
        self._client: Optional[httpx.AsyncClient] = None
        self._token: Optional[str] = None
        self._exp: float = 0.0
        self._base = base_url
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._token_url = f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token"

    async def _ensure_http(self):
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

    async def _get_token(self) -> str:
        if self._token and time.time() < self._exp - 60:
            return self._token
        await self._ensure_http()
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": self._scope,
        }
        resp = await self._client.post(self._token_url, data=data, headers={
            "Content-Type": "application/x-www-form-urlencoded"
        })
        resp.raise_for_status()
        tok = resp.json()
        self._token = tok["access_token"]
        self._exp = time.time() + int(tok.get("expires_in", 3599))
        return self._token

    async def get(self, path: str, params: Optional[Dict[str, str]] = None, consistency_eventual: bool = False):
        token = await self._get_token()
        await self._ensure_http()
        headers = {"Authorization": f"Bearer {token}"}
        if consistency_eventual:
            headers["ConsistencyLevel"] = "eventual"
        url = f"{self._base}{path}"
        r = await self._client.get(url, headers=headers, params=params)
        r.raise_for_status()
        return r.json()

    async def aclose(self):
        if self._client:
            await self._client.aclose()
            self._client = None
