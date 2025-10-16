#!/usr/bin/env python3
"""
Snowflake MCP handler tester — hits the handler (search/fetch), not the low-level client.

Examples:
  # Raw DSL through handler.search()
  python -m tools.snowflake_tool --debug search "list databases"
  python -m tools.snowflake_tool --debug search "db:SNOWFLAKE_SAMPLE_DATA list schemas"
  python -m tools.snowflake_tool --debug search "db:SNOWFLAKE_SAMPLE_DATA schema:TPCDS_SF100TCL list"
  python -m tools.snowflake_tool --debug search "sample db:SNOWFLAKE_SAMPLE_DATA schema:TPCDS_SF100TCL table:CALL_CENTER limit:5"

  # Fetch by id returned from search (note: prefix 'snowflake::' stays)
  python -m tools.snowflake_tool --debug fetch "snowflake::sf://db/SNOWFLAKE_SAMPLE_DATA"

  # Convenience list wrappers (built on handler.search())
  python -m tools.snowflake_tool --debug list databases
  python -m tools.snowflake_tool --debug list schemas --db SNOWFLAKE_SAMPLE_DATA
  python -m tools.snowflake_tool --debug list tables --db SNOWFLAKE_SAMPLE_DATA --schema TPCDS_SF100TCL
"""

import asyncio
import json
import logging
import os
import sys
from argparse import ArgumentParser
from typing import Any, Dict, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Ensure repo root is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from handlers.snowflake import SnowflakeHandler  # noqa: E402

log = logging.getLogger("snowflake_tool")

def _pp(obj: Any):
    print(json.dumps(obj, indent=2, ensure_ascii=False))

# ---------- Handler wrapper ----------
def _mk_handler() -> SnowflakeHandler:
    # Handler internally constructs SnowflakeClient from env
    h = SnowflakeHandler()
    return h

# ---------- Commands ----------
async def cmd_search(handler: SnowflakeHandler, args):
    q = args.query
    log.debug("Handler.search query: %s", q)
    items = await handler.search(q, top=args.top)
    _pp({"results": items})

async def cmd_fetch(handler: SnowflakeHandler, args):
    id_ = args.id
    # Accept either naked sf://... or full "snowflake::sf://..."
    if not id_.startswith("snowflake::"):
        id_ = f"snowflake::{id_}"
    log.debug("Handler.fetch id: %s", id_)
    # Handler.fetch expects the native id (without prefix), main MCP server strips it.
    # So we strip "snowflake::" here before passing to handler.fetch(...)
    native = id_.split("::", 1)[1]
    payload = await handler.fetch(native)
    _pp(payload)

async def cmd_list(handler: SnowflakeHandler, args):
    """
    These are small convenience wrappers that just build a DSL query and call handler.search().
    """
    ent = args.entity
    if ent == "databases":
        q = "list"
    elif ent == "schemas":
        if not args.db:
            raise SystemExit("--db is required for 'list schemas'")
        q = f"db:{args.db} list"
    elif ent == "tables":
        if not (args.db and args.schema):
            raise SystemExit("--db and --schema are required for 'list tables'")
        q = f"db:{args.db} schema:{args.schema} list"
    elif ent == "views":
        if not (args.db and args.schema):
            raise SystemExit("--db and --schema are required for 'list views'")
        # same as tables; handler.list returns both tables & views for a schema,
        # but we’ll filter client-side for display (optional).
        q = f"db:{args.db} schema:{args.schema} list"
    else:
        raise SystemExit(f"Unknown entity: {ent}")

    log.debug("Handler.search(list) query: %s", q)
    items = await handler.search(q, top=args.top)

    # If user asked only views, filter them:
    if ent == "views":
        items = [it for it in items if it.get("type") == "view"]
    if ent == "tables":
        items = [it for it in items if it.get("type") == "table"]

    _pp({"results": items})

# ---------- CLI ----------
def build_parser():
    p = ArgumentParser(description="Snowflake handler tester (search/fetch)")
    p.add_argument("--debug", action="store_true", help="Enable debug logging")

    sub = p.add_subparsers(dest="cmd", required=True)

    sp_s = sub.add_parser("search", help="Call handler.search(query)")
    sp_s.add_argument("query", help="DSL or natural language query")
    sp_s.add_argument("--top", type=int, default=25)
    sp_s.set_defaults(func=cmd_search)

    sp_f = sub.add_parser("fetch", help="Call handler.fetch(id)")
    sp_f.add_argument("id", help="Result id from search (snowflake::sf://...) or bare sf://...")
    sp_f.set_defaults(func=cmd_fetch)

    sp_l = sub.add_parser("list", help="Convenience list using handler.search")
    sp_l.add_argument("entity", choices=["databases", "schemas", "tables", "views"])
    sp_l.add_argument("--db")
    sp_l.add_argument("--schema")
    sp_l.add_argument("--top", type=int, default=50)
    sp_l.set_defaults(func=cmd_list)

    return p

async def _amain():
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="[%(levelname)s] %(message)s")
    # quiet httpx chatter unless you need it
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    h = _mk_handler()
    try:
        await args.func(h, args)
    finally:
        # handler holds an httpx client via SnowflakeClient; close it if exposed
        if hasattr(h, "sf") and hasattr(h.sf, "aclose"):
            await h.sf.aclose()

def main():
    asyncio.run(_amain())

if __name__ == "__main__":
    main()
