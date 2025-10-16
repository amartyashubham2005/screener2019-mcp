# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modular, scalable MCP (Model Context Protocol) server built with Python and FastAPI. It provides unified search and fetch APIs across multiple data sources (Outlook, Snowflake, Box) with JWT authentication, user management, and dynamic handler allocation based on gateway domains.

## Development Commands

### Environment Setup

Always activate the virtual environment before running commands:

```bash
# Create venv
python3.12 -m venv .venv

# Activate venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Database Operations

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Rollback last migration
alembic downgrade -1

# Check migration status
alembic current
```

### Running the Server

```bash
# Development (manual)
python3.12 main.py

# Production with PM2 (auto-restart, runs on boot)
pm2 start "bash -lc 'source .venv/bin/activate && pip3 install -r requirements.txt && python3.12 main.py'" --name mcp-server
pm2 save
pm2 startup  # Follow printed instructions

# PM2 management
pm2 logs mcp-server    # View logs
pm2 restart mcp-server # Restart
pm2 stop mcp-server    # Stop
pm2 delete mcp-server  # Remove from PM2
```

## Architecture

### Core Structure

The application uses a layered architecture with clear separation of concerns:

1. **main.py** - Entry point containing:
   - FastAPI/FastMCP server initialization
   - Route registration (auth, CRUD, health check)
   - Dynamic handler allocation logic based on request domain
   - MCP tools: `search()` and `fetch()` that aggregate across handlers

2. **handlers/** - Pluggable data source handlers:
   - `base.py` - Abstract `BaseHandler` class with `_search_impl()` and `_fetch_impl()` methods
   - Each handler (Outlook, Snowflake, Box) implements the base interface
   - Handlers are instantiated dynamically per request based on the MCP gateway domain

3. **services/** - External API clients:
   - `graph_client.py` - Microsoft Graph API for Outlook
   - `snowflake_cortex_client.py` - Snowflake REST SQL API
   - `box_client.py` - Box API integration

4. **database/** - Data layer:
   - `config.py` - SQLAlchemy async engine and session factory
   - `models.py` - SQLAlchemy ORM models (User, Source, MCPServer)

5. **repositories/** - Data access layer:
   - `user_repository.py` - User CRUD operations
   - `source_repository.py` - Source CRUD with user isolation
   - `mcp_server_repository.py` - MCP server CRUD with endpoint allocation

6. **schemas/** - Pydantic models for request/response validation

7. **auth/** - JWT utilities and password hashing with bcrypt

### Key Architectural Patterns

**Dynamic Handler Allocation:**
The server uses domain-based handler allocation. Each MCP server gets a unique endpoint from `MCP_GATEWAY_URL_POOLS`. When a request comes in:

1. Extract domain from `get_http_request().url`
2. Query database for MCP servers with matching endpoint
3. Load associated sources for that server
4. Instantiate handlers based on source types (Outlook/Snowflake/Box)
5. Execute search/fetch across all handlers

This pattern is implemented in functions like `get_outlook_handlers_for_current_domain()` in main.py around lines 865-927.

**Handler Pattern:**
All handlers inherit from `BaseHandler` and implement:
- `_search_impl(query, top)` - Returns list of search results
- `_fetch_impl(native_id)` - Returns full object details
- `id_prefix` - Used for routing fetch requests (e.g., "outlook::", "snowflake::")

**Repository Pattern:**
All database access goes through repository classes that provide:
- User isolation (all queries filter by user_id)
- Async operations using SQLAlchemy + asyncpg
- Proper transaction management with explicit commits

## Environment Variables

Required in `.env` file:

- `DATABASE_URL` - PostgreSQL async connection string (postgresql+asyncpg://...)
- `JWT_SECRET` - Secret key for JWT token signing
- `OPENAI_API_KEY` - OpenAI API key (for integrations)
- `MCP_GATEWAY_URL_POOLS` - Comma-separated list of gateway domains for MCP server allocation

## API Endpoints

### Authentication
- `POST /api/v1/signup` - Register user
- `POST /api/v1/signin` - Login (returns JWT in cookie)
- `POST /api/v1/signout` - Logout (clears cookie)
- `GET /api/v1/me` - Get current user (requires JWT cookie)

### Sources
- `GET /api/v1/sources` - List user's sources
- `POST /api/v1/sources` - Create source
- `GET /api/v1/sources/{id}` - Get source
- `PUT /api/v1/sources/{id}` - Update source
- `DELETE /api/v1/sources/{id}` - Delete source

### MCP Servers
- `GET /api/v1/mcp-servers` - List user's MCP servers
- `POST /api/v1/mcp-servers` - Create MCP server (auto-assigns endpoint)
- `GET /api/v1/mcp-servers/{id}` - Get MCP server
- `PUT /api/v1/mcp-servers/{id}` - Update MCP server
- `DELETE /api/v1/mcp-servers/{id}` - Soft delete MCP server

### MCP Tools
- `search(query)` - Aggregated search across all handlers for current domain
- `fetch(id)` - Fetch details by ID (routed by prefix: outlook::, snowflake::, box::)

### Health
- `GET /api/v1/checks` - Health check with handler counts and uptime

## Database Schema

### users
- `id` (UUID PK)
- `email` (unique, indexed)
- `hashed_password` (bcrypt)
- `created_at`, `updated_at`

### sources
- `id` (UUID PK)
- `type` (string: "outlook", "snowflake", "box")
- `source_metadata` (JSONB: credentials and config)
- `user_id` (FK to users, CASCADE delete)
- `created_at`, `updated_at`

### mcp_servers
- `id` (UUID PK)
- `name` (string)
- `endpoint` (string: auto-assigned from pool)
- `source_ids` (array of UUIDs as strings)
- `user_id` (FK to users, CASCADE delete)
- `created_at`, `updated_at`, `deleted_at` (soft delete)

## Testing

Test scripts in root directory:
- `test_auth_api.py` - Authentication endpoint tests
- `test_sources_api.sh` - Source CRUD tests
- `test_mcp_servers_api.sh` - MCP server CRUD tests

Run with:
```bash
python test_auth_api.py
bash test_sources_api.sh
bash test_mcp_servers_api.sh
```

## Important Implementation Notes

1. **Always use async/await** - All database operations are async with SQLAlchemy + asyncpg

2. **Session management** - Use `async for db in get_db():` context manager pattern, never manually create sessions

3. **Explicit commits** - After database writes, call `await db.commit()` explicitly

4. **User isolation** - All repository methods automatically filter by user_id for security

5. **Handler lifecycle** - Handlers are instantiated per-request based on the incoming domain, not stored globally

6. **CORS** - CORS headers are added to all responses via helper functions in main.py

7. **JWT in cookies** - Authentication uses HTTP-only cookies, not Authorization headers

8. **Soft deletion** - MCP servers use soft deletion (deleted_at timestamp), not hard deletes

9. **Endpoint allocation** - MCP server endpoints are auto-assigned from `MCP_GATEWAY_URL_POOLS` on creation and cannot be changed

10. **Source metadata validation** - Use `SourceValidator.validate_metadata()` from utils/ when creating or updating sources

## Adding New Handlers

To add a new data source handler:

1. Create handler class in `handlers/` inheriting from `BaseHandler`
2. Implement `_search_impl()` and `_fetch_impl()`
3. Set `id_prefix` (e.g., "newhandler")
4. Create API client in `services/` if needed
5. Add metadata validation in `utils/source_validator.py`
6. Add handler allocation function in main.py (e.g., `get_newhandler_handlers_for_current_domain()`)
7. Include in search/fetch aggregation in main.py

## Troubleshooting

- **"No available domains in MCP_GATEWAY_URL_POOLS"** - Add more URLs to .env and configure reverse proxy
- **Database connection errors** - Check DATABASE_URL format and PostgreSQL is running
- **JWT/auth issues** - Verify JWT_SECRET is set and cookies are being sent
- **Handler not loading** - Check source metadata is complete and matches validation schema
