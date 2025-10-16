
# Modular MCP Server (Python)

## Overview
This project is a modular, scalable MCP (Model Context Protocol) server written in Python. It provides unified search and fetch APIs across multiple data sources (Outlook, Snowflake, Box) and supports user authentication, source management, and dynamic handler allocation based on gateway domains. The server is built on FastAPI and Starlette, with async database operations and JWT-based authentication.

## Features
- JWT-based authentication (signup, signin, signout, protected endpoints)
- User, Source, and MCP Server CRUD APIs
- Pluggable handlers for Outlook (Microsoft Graph), Snowflake (REST SQL API), and Box
- Dynamic handler allocation based on MCP gateway domain
- Health check endpoint
- CORS support for development and production
- Modular, extensible architecture

## Architecture
- **main.py**: Entry point, route registration, handler orchestration, authentication, and CRUD logic
- **handlers/**: Pluggable handler classes for each data source (Outlook, Snowflake, Box)
- **services/**: API clients for external services (Graph, Snowflake, Box)
- **database/**: SQLAlchemy async models and config
- **repositories/**: Data access layer for users, sources, and MCP servers
- **schemas/**: Pydantic models for request/response validation
- **auth/**: JWT utilities and password hashing

## Environment Variables
Set these in your `.env` file:

| Variable                | Description |
|-------------------------|-------------|
| `OPENAI_API_KEY`        | OpenAI API key for integrating with OpenAI services. |
| `DATABASE_URL`          | PostgreSQL async connection string (e.g. `postgresql+asyncpg://user:pass@host:port/dbname`). |
| `JWT_SECRET`            | Secret key for signing JWT tokens (used for authentication). |
| `MCP_GATEWAY_URL_POOLS` | Comma-separated list of MCP gateway URLs. Each MCP server is assigned one. |

**Adding More Gateway URLs:**
To support more MCP servers, add new URLs to `MCP_GATEWAY_URL_POOLS` (comma-separated). You must also configure these URLs at your reverse proxy/load balancer before they can be allocated by the server.

## Installation & Setup (updated)

### Prerequisites

* **Python 3.12** installed and available as `python3.12` (verify with `python3.12 --version`).
* `git` (optional, to clone the repo).
* Access to your `.env` values (see `.env.template`).

### Create & activate a venv (recommended)

1. Create the venv (run from the project root):

```bash
python3.12 -m venv .venv
```

2. Activate the venv:

* macOS / Linux (bash, zsh):

```bash
source .venv/bin/activate
```

* Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

* Windows CMD:

```cmd
.venv\Scripts\activate.bat
```

3. Confirm you're using the venv's Python and right version:

```bash
which python    # should point to .venv/bin/python (or .venv\Scripts\python on windows)
python --version  # should show Python 3.12.x
```

### Install dependencies

With the venv active:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

(Optionally pin / freeze after install:)

```bash
pip freeze > requirements-lock.txt
```

### Configure environment

```bash
cp .env.template .env
# edit .env and fill in secrets (OPENAI_API_KEY, DATABASE_URL, JWT_SECRET, MCP_GATEWAY_URL_POOLS, etc.)
```

**Important:** Always activate the venv before running commands that depend on the project environment (migrations, tests, server start).

### Database setup

With the venv active, run migrations:

```bash
alembic upgrade head
```

(See `DATABASE_SETUP.md` for schema details and any manual steps.)

### Start the server


```bash
python3.12 main.py
```


### Notes

* Always activate the venv before running `alembic`, `python main.py`, `uvicorn`, or any management script so the correct Python interpreter and dependencies are used.
* If you use a system package manager (pyenv, asdf), make sure the `python3.12` in your PATH points to the intended interpreter.
* For CI/CD, mirror the same steps: install Python 3.12 runtime, create/activate venv (or use the runner's virtual env), then `pip install -r requirements.txt`, run migrations, then start the service.


## Run the server continuously with PM2 (recommended for production)

PM2 is a lightweight process manager that keeps your Python server running even after you close the terminal or the host machine reboots.

### 1. Install PM2 globally

```bash
npm i -g pm2
```

### 2. Start the MCP server with PM2

From the project root:

```bash
pm2 start "bash -lc 'source .venv/bin/activate && pip3 install -r requirements.txt && python3.12 main.py'" --name mcp-server
```

> 💡 This command:
>
> * Activates your virtual environment (`.venv`)
> * Ensures dependencies are installed
> * Launches the Python MCP server via PM2

### 3. Save the process list

```bash
pm2 save
```

This ensures PM2 remembers to restart the process automatically after a reboot.

### 4. Enable startup on system boot

```bash
pm2 startup
```

PM2 will print a system command for your environment — it typically looks like this:

```bash
sudo env PATH=$PATH:/home/user2/.nvm/versions/node/v20.10.0/bin \
/home/user2/.nvm/versions/node/v20.10.0/lib/node_modules/pm2/bin/pm2 \
startup systemd -u user2@asysltd.onmicrosoft.com --hp /home/user2
```

Copy and run that command exactly once. It registers PM2 with `systemd` so the server starts automatically on boot.

### 5. Common management commands

| Command                  | Description                                             |
| ------------------------ | ------------------------------------------------------- |
| `pm2 status`             | View running processes                                  |
| `pm2 logs mcp-server`    | Stream logs from the app                                |
| `pm2 restart mcp-server` | Restart the app                                         |
| `pm2 stop mcp-server`    | Stop the app                                            |
| `pm2 delete mcp-server`  | Remove from PM2’s list                                  |
| `pm2 save`               | Save the current process list (important after changes) |

### 6. Example session

```bash
npm i -g pm2
pm2 start 'source venv/bin/activate && pip3 install -r requirements.txt && python3.12 main.py' --name mcp-server
pm2 save
pm2 startup # might need to re-login or run some command
pm2 logs mcp-server
pm2 restart mcp-server
```

After this setup:

* The backend will automatically restart if it crashes.
* It will also start automatically on system boot.
* Logs can be viewed with `pm2 logs mcp-server`.


## API Endpoints

### Authentication
- `POST /api/v1/signup` — Register a new user
- `POST /api/v1/signin` — Authenticate and receive JWT token
- `POST /api/v1/signout` — Sign out (clears cookie)
- `GET /api/v1/me` — Get current user info

### Sources
- `GET /api/v1/sources` — List all sources for user
- `POST /api/v1/sources` — Create a new source (Outlook, Box, Snowflake)
- `GET /api/v1/sources/{id}` — Get source by ID
- `PUT /api/v1/sources/{id}` — Update source
- `DELETE /api/v1/sources/{id}` — Delete source

### MCP Servers
- `GET /api/v1/mcp-servers` — List MCP servers for user
- `POST /api/v1/mcp-servers` — Create MCP server (allocates endpoint from pool)
- `GET /api/v1/mcp-servers/{id}` — Get MCP server by ID
- `PUT /api/v1/mcp-servers/{id}` — Update MCP server
- `DELETE /api/v1/mcp-servers/{id}` — Delete MCP server

### Search & Fetch
- `search(query)` — Aggregated search across all enabled handlers (Outlook, Snowflake, Box)
- `fetch(id)` — Fetch details by ID, routed to correct handler by prefix

### Health & Fallback
- `GET /api/v1/checks` — Health check (shows handler counts, uptime)
- All other routes return a fallback 404 with request details

## Handler Details
- **OutlookHandler**: Searches and fetches emails via Microsoft Graph API. Requires tenant/client/user credentials in source metadata.
- **SnowflakeCortexHandler**: Searches and fetches Snowflake DB objects via REST SQL API. Requires account URL, PAT, semantic model file, and search service in source metadata.
- **BoxHandler**: Searches and fetches Box files via Box API. Requires client credentials and subject info in source metadata.

Handlers are dynamically allocated per MCP server domain, based on the sources assigned to that server.

## Authentication
- JWT tokens are issued on signin and stored in HTTP-only cookies
- Passwords are hashed with bcrypt
- All protected endpoints require a valid JWT token
- See `README_AUTH.md` for full authentication API details and examples

## Database Schema
- See `DATABASE_SETUP.md` for full schema and migration instructions
- Tables: `users`, `sources`, `mcp_servers` (with relationships and soft deletion)

## Adding More MCP Gateway URLs
1. Add the new URL to `MCP_GATEWAY_URL_POOLS` in `.env` (comma-separated)
2. Update your reverse proxy/load balancer to route traffic for the new domain
3. New MCP servers will be assigned available domains from the pool automatically

## Development Notes
- CORS is enabled for local development and production origins
- All async DB operations use SQLAlchemy and asyncpg
- Modular handler architecture for easy extension

## Troubleshooting
- If you see `No available domains in MCP_GATEWAY_URL_POOLS`, add more URLs to the pool and update your proxy config
- For DB errors, check your connection string and run migrations
- For authentication issues, verify your JWT secret and cookie settings

---
For further details, see `DATABASE_SETUP.md` and `README_AUTH.md`. For questions, contact the project maintainer.
