import logging
import os
import re
import json
from typing import Any, Dict, List, Optional, Tuple
import uuid

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SnowflakeCortexClient:
    """
    Minimal async client for Snowflake SQL API v2 (REST).
    Read-only: you should only pass SELECT / DESCRIBE / SHOW statements.
    """

    def __init__(
        self,
        semantic_model_file: str,
        cortex_search_service: str,
        snowflake_account_url: str,
        snowflake_pat: str,
    ):
        if not snowflake_pat:
            raise RuntimeError("snowflake_pat is required")
        if not snowflake_account_url:
            raise RuntimeError("snowflake_account_url is required")
        if not semantic_model_file:
            raise RuntimeError("semantic_model_file is required")
        if not cortex_search_service:
            raise RuntimeError("cortex_search_service is required")

        self.semantic_model_file = semantic_model_file
        self.cortex_search_service = cortex_search_service
        self.snowflake_account_url = snowflake_account_url
        self.snowflake_pat = snowflake_pat
        
        # Headers for API requests
        self.api_headers = {
            "Authorization": f"Bearer {self.snowflake_pat}",
            "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
            "Content-Type": "application/json",
        }

    async def process_sse_response(self, resp: httpx.Response) -> Tuple[str, str, List[Dict]]:
        """
        Parse Snowflake Cortex Agent SSE. Handles dict, list, nested lists, and JSON strings.
        Returns (text, sql, citations).
        """

        def _iter_event_dicts(obj):
            """Yield dict events from obj (dict | list | nested lists | json string)."""
            if obj is None:
                return
            if isinstance(obj, dict):
                yield obj
                return
            if isinstance(obj, list):
                for it in obj:
                    # Items might themselves be strings or lists
                    yield from _iter_event_dicts(it)
                return
            if isinstance(obj, str):
                # Some frames are JSON strings (e.g., OpenTelemetry traces)
                try:
                    parsed = json.loads(obj)
                    yield from _iter_event_dicts(parsed)
                except Exception:
                    return  # ignore non-JSON strings

        def _get_delta(ev: Dict) -> Optional[Dict]:
            # Common shapes:
            # {"delta": {...}} OR {"data": {"delta": {...}}}
            d = ev.get("delta")
            if isinstance(d, dict):
                return d
            data = ev.get("data")
            if isinstance(data, dict):
                d2 = data.get("delta")
                if isinstance(d2, dict):
                    return d2
            return None

        text_parts: List[str] = []
        sql: Optional[str] = None
        citations: List[Dict] = []

        async for raw_line in resp.aiter_lines():
            if not raw_line:
                continue
            line = raw_line.strip()
            if not line.startswith("data:"):
                continue

            payload = line[5:].strip()
            if not payload or payload == "[DONE]":
                continue

            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                # Ignore keepalives / comments
                continue

            for evt in _iter_event_dicts(parsed):
                # (Optional) skip obvious telemetry envelopes
                if isinstance(evt, dict) and evt.get("name") == "Agent" and "attributes" in evt:
                    continue

                delta = _get_delta(evt)
                if not isinstance(delta, dict):
                    # Some providers put SQL directly at top-level too
                    if isinstance(evt, dict) and not sql:
                        top_sql = evt.get("sql")
                        if isinstance(top_sql, str):
                            sql = top_sql
                    continue

                # 1) Primary content stream
                content = delta.get("content", [])
                if isinstance(content, dict):
                    content = [content]

                if isinstance(content, list):
                    for item in content:
                        if not isinstance(item, dict):
                            continue
                        t = item.get("type")

                        # Text tokens
                        if t == "text":
                            part = item.get("text")
                            if isinstance(part, str):
                                text_parts.append(part)

                        # Tool use (e.g., sql_exec inputs) – optionally capture SQL input as a fallback
                        elif t == "tool_use":
                            tu = item.get("tool_use") or {}
                            if not sql and isinstance(tu, dict):
                                if tu.get("type") == "sql_exec":
                                    inp = tu.get("input")
                                    if isinstance(inp, dict):
                                        q = inp.get("query")
                                        if isinstance(q, str) and q.strip():
                                            sql = q  # fallback if tool_results don't return sql

                        # Tool results (Analyst1 emits sql + text here)
                        elif t == "tool_results":
                            tr = item.get("tool_results")
                            if not isinstance(tr, dict):
                                continue
                            tr_content = tr.get("content", [])
                            if isinstance(tr_content, dict):
                                tr_content = [tr_content]

                            for res in tr_content:
                                if not isinstance(res, dict):
                                    continue
                                if res.get("type") == "json":
                                    j = res.get("json", {})
                                    if not isinstance(j, dict):
                                        continue

                                    # Textual explanation
                                    j_text = j.get("text")
                                    if isinstance(j_text, str):
                                        text_parts.append(j_text)

                                    # Capture SQL (first one wins)
                                    if "sql" in j and not sql:
                                        s = j.get("sql")
                                        if isinstance(s, str):
                                            sql = s

                                    # Citations
                                    sr = j.get("searchResults", [])
                                    if isinstance(sr, list):
                                        for sres in sr:
                                            if isinstance(sres, dict):
                                                citations.append({
                                                    "source_id": sres.get("source_id"),
                                                    "doc_id": sres.get("doc_id"),
                                                })

                # 2) Some frames stream sql directly in delta
                if not sql:
                    dsql = delta.get("sql")
                    if isinstance(dsql, str):
                        sql = dsql

                # 3) Optional finish signal
                finish = delta.get("finish_reason")
                if finish in ("stop", "completed"):
                    # We can break if desired; leaving as no-op to keep consuming safely
                    pass

        return "".join(text_parts), (sql or ""), citations

    async def execute_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL using the Snowflake SQL API.
        
        Args:
            sql: The SQL query to execute
            
        Returns:
            Dict containing either the query results or an error message
        """
        try:
            # Generate a unique request ID
            request_id = str(uuid.uuid4())
            
            # Prepare the SQL API request
            sql_api_url = f"{self.snowflake_account_url}/api/v2/statements"
            sql_payload = {
                "statement": sql.replace(";", ""),
                "timeout": 60  # 60 second timeout
            }
            
            async with httpx.AsyncClient() as client:
                sql_response = await client.post(
                    sql_api_url,
                    json=sql_payload,
                    headers=API_HEADERS,
                    params={"requestId": request_id}
                )
                
                if sql_response.status_code == 200:
                    return sql_response.json()
                else:
                    return {"error": f"SQL API error: {sql_response.text}"}
        except Exception as e:
            return {"error": f"SQL execution error: {e}"}

    async def run_cortex_agents(self, query: str) -> Dict[str, Any]:
        """Run the Cortex agent with the given query, streaming SSE."""
        # Build your payload exactly as before
        payload = {
            "model": "claude-3-5-sonnet",
            "response_instruction": "You are a helpful AI assistant.",
            "experimental": {},
            "tools": [
                {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "Analyst1"}},
                {"tool_spec": {"type": "cortex_search",            "name": "Search1"}},
                {"tool_spec": {"type": "sql_exec",                "name": "sql_execution_tool"}},
            ],
            "tool_resources": {
                "Analyst1": {"semantic_model_file": self.semantic_model_file},
                "Search1":  {"name": self.cortex_search_service},
            },
            "tool_choice": {"type": "auto"},
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": query}]}
            ],
        }

        # (Optional) generate a request ID if you want traceability
        request_id = str(uuid.uuid4())

        url = f"{self.snowflake_account_url}/api/v2/cortex/agent:run"
        # Copy your API headers and add the SSE Accept
        headers = {
            **self.api_headers,
            "Accept": "text/event-stream",
        }

        print('payload', payload)
        print('headers', headers)

        # 1) Open a streaming POST
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                url,
                json=payload,
                headers=headers,
                params={"requestId": request_id},   # SQL API needs this, Cortex agent may ignore it
            ) as resp:
                resp.raise_for_status()
                # 2) Now resp.aiter_lines() will yield each "data: …" chunk
                text, sql, citations = await self.process_sse_response(resp)

        # 3) If SQL was generated, execute it
        results = await self.execute_sql(sql) if sql else None
        print('results', results)
        print('text', text)
        print('sql', sql)
        print('citations', citations)

        return {
            "text": text,
            "citations": citations,
            "sql": sql,
            "results": results,
        }

        # return {
        #     "id": json.stringify({
        #         "text": text,
        #         "citations": citations,
        #         "sql": sql,
        #         "results": results,
        #     })
        # }

