# ---------------------------
# Bootstrap & logging (MUST BE FIRST)
# ---------------------------
from dotenv import load_dotenv
load_dotenv()  # Load environment variables before importing anything else

import logging
import time
import uuid

from typing import Dict, List, Any

from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request
from starlette.responses import JSONResponse

# Handlers
from handlers.outlook import OutlookHandler
from handlers.snowflake_cortex import SnowflakeCortexHandler
from handlers.box import BoxHandler

# Database
from database.config import get_db
from repositories.mcp_server_repository import MCPServerRepository
from repositories.source_repository import SourceRepository

import urllib.parse
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVER_INSTRUCTIONS = """
This MCP server exposes `search` and `fetch` via pluggable handlers.

Currently enabled:
- Outlook email via Microsoft Graph (Application permissions)
- Snowflake via REST SQL API v2 (Bearer token)

Usage:
- search(query) -> aggregates results from all handlers
    - Outlook: search across folders (default inbox)
    - Snowflake: search across databases, schemas, tables, and views
- fetch(id)     -> routed to the correct handler by id prefix:
    - 'outlook::xxxx'      -> Outlook handler
    - 'snowflake::db/...'  -> Snowflake database (lists schemas)
    - 'snowflake::schema/DB.SCHEMA' -> Snowflake schema (lists tables & views)
    - 'snowflake::table/DB.SCHEMA.TABLE' -> Snowflake table (columns + sample rows)
    - 'snowflake::view/DB.SCHEMA.VIEW'   -> Snowflake view (columns + sample rows)

Example queries:
- search("project update in:sent")
- search("call_center")
- fetch("snowflake::table/SNOWFLAKE_SAMPLE_DATA.TPCDS_SF100TCL.CALL_CENTER")
"""

START_TIME = time.time()

def add_cors_headers(response, request=None):
    """Add CORS headers to response for development."""
    # Get origin from request or use default development origins
    origin = None
    if request:
        origin = request.headers.get("origin")
    
    # List of allowed origins for development
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "https://jesterbot.com"
    ]
    
    # If origin is in allowed list, use it; otherwise use first allowed origin
    if origin and origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = allowed_origins[0]
    
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Cookie"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

def cors_json_response(content, status_code=200, request=None):
    """Create a JSONResponse with CORS headers."""
    response = JSONResponse(content, status_code=status_code)
    return add_cors_headers(response, request)

def cors_error_response(detail, status_code=400, request=None):
    """Create an error JSONResponse with CORS headers."""
    return cors_json_response({"detail": detail}, status_code, request)

def register_auth_routes(mcp: FastMCP):
    """Register authentication routes as custom routes."""
    from database.config import get_db
    from repositories.user_repository import UserRepository
    from schemas.schemas import UserCreate, UserLogin
    from auth.utils import AuthUtils
    
    # Add OPTIONS handler for CORS preflight
    @mcp.custom_route("/api/v1/{path:path}", methods=["OPTIONS"])
    async def handle_cors(request: Request):
        response = JSONResponse({})
        return add_cors_headers(response, request)

    # Signup endpoint
    @mcp.custom_route("/api/v1/signup", methods=["POST"])
    async def signup(request: Request):
        try:
            body = await request.json()
            user_data = UserCreate(**body)
            
            # Use proper async context manager for database session
            async for db in get_db():
                user_repo = UserRepository(db)
                
                # Check if user already exists
                existing_user = await user_repo.get_by_email(user_data.email)
                if existing_user:
                    return cors_error_response("Email already registered", 400, request)
                
                # Hash password and create user
                hashed_password = AuthUtils.hash_password(user_data.password)
                user = await user_repo.create({
                    "email": user_data.email,
                    "hashed_password": hashed_password
                })
                
                # Explicitly commit the transaction
                await db.commit()
                
                response = JSONResponse({
                    "id": str(user.id),
                    "email": user.email,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat()
                })
                return add_cors_headers(response, request)
                
        except Exception as e:
            print(e)
            return cors_error_response(str(e), 400, request)

    # Signin endpoint
    @mcp.custom_route("/api/v1/signin", methods=["POST"])
    async def signin(request: Request):
        try:
            body = await request.json()
            user_data = UserLogin(**body)
            
            # Use proper async context manager for database session
            async for db in get_db():
                user_repo = UserRepository(db)
                
                # Get user by email
                user = await user_repo.get_by_email(user_data.email)
                if not user or not AuthUtils.verify_password(user_data.password, user.hashed_password):
                    return cors_error_response("Invalid email or password", 401, request)
                
                # Create access token
                access_token = AuthUtils.create_access_token(user.email)
                
                # Create response with cookie
                response = JSONResponse({
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "full_name": ""
                    }
                })
                
                # Set HTTP-only cookie
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=True,
                    samesite="lax",  # Change to lax for cross-origin cookies
                    max_age=24 * 60 * 60  # 24 hours
                )
                
                return add_cors_headers(response, request)
                
        except Exception as e:
            print(e)
            return cors_error_response(str(e), 400, request)

    # Signout endpoint
    @mcp.custom_route("/api/v1/signout", methods=["POST"])
    async def signout(request: Request):
        response = JSONResponse({"message": "Successfully signed out"})
        response.delete_cookie(
            key="access_token",
            httponly=True,
            secure=False,  # Set to False for development
            samesite="lax"  # Change to lax for cross-origin cookies
        )
        return add_cors_headers(response, request)

    # Helper function to get current user from request
    async def get_current_user_from_request(request: Request):
        """Extract and validate user from request cookies. Returns email or error response."""
        cookies = request.headers.get("Cookie")
        token = AuthUtils.extract_token_from_cookies(cookies)
        
        if not token:
            return None, cors_error_response("Access token required in cookies", 401, request)
        
        payload = AuthUtils.decode_access_token(token)
        if not payload:
            return None, cors_error_response("Invalid or expired token", 401, request)
        
        email = payload.get("email")
        if not email:
            return None, cors_error_response("Invalid token payload", 401, request)
        
        return email, None

    # Me endpoint (protected)
    @mcp.custom_route("/api/v1/me", methods=["GET"])
    async def get_current_user(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        # Get user from database with proper session management
        async for db in get_db():
            user_repo = UserRepository(db)
            user = await user_repo.get_by_email(email)
            if not user:
                return cors_error_response("User not found", 401, request)
            
            response = JSONResponse({
                "id": str(user.id),
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            })
            return add_cors_headers(response, request)

    # Sources CRUD endpoints
    
    # GET /api/v1/sources - List all sources for user
    @mcp.custom_route("/api/v1/sources", methods=["GET"])
    async def list_sources(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        # Get user and sources with proper session management
        async for db in get_db():
            user_repo = UserRepository(db)
            user = await user_repo.get_by_email(email)
            if not user:
                return cors_error_response("User not found", 401, request)
            
            from repositories.source_repository import SourceRepository
            source_repo = SourceRepository(db)
            sources = await source_repo.get_user_sources(user.id)
            
            sources_data = []
            for source in sources:
                sources_data.append({
                    "id": str(source.id),
                    "type": source.type,
                    "source_metadata": source.source_metadata,  # Already a dict, not stringified
                    "created_at": source.created_at.isoformat(),
                    "updated_at": source.updated_at.isoformat()
                })
            
            return cors_json_response(sources_data, 200, request)

    # GET /api/v1/sources/{id} - Get source by ID for user
    @mcp.custom_route("/api/v1/sources/{source_id}", methods=["GET"])
    async def get_source(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        source_id = request.path_params.get("source_id")
        
        try:
            source_uuid = uuid.UUID(source_id)
        except ValueError:
            return cors_error_response("Invalid source ID format", 400, request)
        
        # Get user and source with proper session management
        async for db in get_db():
            user_repo = UserRepository(db)
            user = await user_repo.get_by_email(email)
            if not user:
                return cors_error_response("User not found", 401, request)
            
            from repositories.source_repository import SourceRepository
            source_repo = SourceRepository(db)
            
            # Check if source belongs to user
            if not await source_repo.source_belongs_to_user(source_uuid, user.id):
                return cors_error_response("Source not found", 404, request)
            
            source = await source_repo.get_source_by_id(source_uuid)
            if not source:
                return cors_error_response("Source not found", 404, request)
            
            return cors_json_response({
                "id": str(source.id),
                "type": source.type,
                "source_metadata": source.source_metadata,
                "created_at": source.created_at.isoformat(),
                "updated_at": source.updated_at.isoformat()
            }, 200, request)

    # POST /api/v1/sources - Create source for user
    @mcp.custom_route("/api/v1/sources", methods=["POST"])
    async def create_source(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        try:
            body = await request.json()
            from schemas.schemas import SourceCreate
            from utils.source_validator import SourceValidator
            
            # Validate basic structure
            source_data = SourceCreate(**body)
            
            # Validate metadata based on source type
            validated_metadata = SourceValidator.validate_metadata(
                source_data.type, 
                source_data.source_metadata
            )
            
            # Create source with proper session management
            async for db in get_db():
                user_repo = UserRepository(db)
                user = await user_repo.get_by_email(email)
                if not user:
                    return cors_error_response("User not found", 401, request)
                
                from repositories.source_repository import SourceRepository
                source_repo = SourceRepository(db)
                
                source = await source_repo.create_source(
                    user_id=user.id,
                    source_type=source_data.type,
                    metadata=validated_metadata
                )
                
                await db.commit()
                
                return cors_json_response({
                    "id": str(source.id),
                    "type": source.type,
                    "source_metadata": source.source_metadata,
                    "created_at": source.created_at.isoformat(),
                    "updated_at": source.updated_at.isoformat()
                }, 201, request)
            
        except ValueError as e:
            return cors_error_response(str(e), 400, request)
        except Exception as e:
            return cors_error_response(str(e), 400, request)

    # PUT /api/v1/sources/{id} - Update source for user
    @mcp.custom_route("/api/v1/sources/{source_id}", methods=["PUT"])
    async def update_source(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        source_id = request.path_params.get("source_id")
        
        try:
            source_uuid = uuid.UUID(source_id)
        except ValueError:
            return cors_error_response("Invalid source ID format", 400, request)
        
        try:
            body = await request.json()
            from schemas.schemas import SourceUpdate
            from utils.source_validator import SourceValidator
            from repositories.source_repository import SourceRepository
            
            # Validate update data
            update_data = SourceUpdate(**body)
            
            # Update source with proper session management
            async for db in get_db():
                user_repo = UserRepository(db)
                user = await user_repo.get_by_email(email)
                if not user:
                    return cors_error_response("User not found", 401, request)
                
                source_repo = SourceRepository(db)
                
                # Check if source belongs to user
                if not await source_repo.source_belongs_to_user(source_uuid, user.id):
                    return cors_error_response("Source not found", 404, request)
                
                # Prepare values for update
                new_source_type = None
                new_metadata = None
                
                if update_data.type is not None:
                    new_source_type = update_data.type
                    
                if update_data.source_metadata is not None:
                    # Use the new type if provided, otherwise get current type
                    source_type = update_data.type
                    if source_type is None:
                        current_source = await source_repo.get_source_by_id(source_uuid)
                        source_type = current_source.type
                    
                    # Validate metadata
                    new_metadata = SourceValidator.validate_metadata(
                        source_type, 
                        update_data.source_metadata
                    )
                
                if new_source_type is None and new_metadata is None:
                    return cors_error_response("No valid fields to update", 400, request)
                
                # Update source
                success = await source_repo.update_source(
                    source_uuid, 
                    source_type=new_source_type,
                    metadata=new_metadata
                )
                if not success:
                    return cors_error_response("Source not found", 404, request)
                
                await db.commit()
                
                # Return updated source
                updated_source = await source_repo.get_source_by_id(source_uuid)
                return cors_json_response({
                    "id": str(updated_source.id),
                    "type": updated_source.type,
                    "source_metadata": updated_source.source_metadata,
                    "created_at": updated_source.created_at.isoformat(),
                    "updated_at": updated_source.updated_at.isoformat()
                }, 200, request)
            
        except ValueError as e:
            return cors_error_response(str(e), 400, request)
        except Exception as e:
            return cors_error_response(str(e), 400, request)

    # DELETE /api/v1/sources/{id} - Delete source for user
    @mcp.custom_route("/api/v1/sources/{source_id}", methods=["DELETE"])
    async def delete_source(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        source_id = request.path_params.get("source_id")
        
        try:
            source_uuid = uuid.UUID(source_id)
        except ValueError:
            return cors_error_response("Invalid source ID format", 400, request)
        
        # Delete source with proper session management
        async for db in get_db():
            user_repo = UserRepository(db)
            user = await user_repo.get_by_email(email)
            if not user:
                return cors_error_response("User not found", 401, request)
            
            from repositories.source_repository import SourceRepository
            source_repo = SourceRepository(db)
            
            # Check if source belongs to user
            if not await source_repo.source_belongs_to_user(source_uuid, user.id):
                return cors_error_response("Source not found", 404, request)
            
            # Delete source
            success = await source_repo.delete_source(source_uuid)
            if not success:
                return cors_error_response("Source not found", 404, request)
            
            await db.commit()
            
            return cors_json_response({"message": "Source deleted successfully"}, 200, request)

    # MCP Servers CRUD endpoints
    
    # GET /api/v1/mcp-servers - List all MCP servers for user
    @mcp.custom_route("/api/v1/mcp-servers", methods=["GET"])
    async def list_mcp_servers(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        # Get user and MCP servers with proper session management
        async for db in get_db():
            user_repo = UserRepository(db)
            user = await user_repo.get_by_email(email)
            if not user:
                return cors_error_response("User not found", 401, request)
            
            from repositories.mcp_server_repository import MCPServerRepository
            server_repo = MCPServerRepository(db)
            servers = await server_repo.get_user_mcp_servers(user.id)
            
            servers_data = []
            for server in servers:
                servers_data.append({
                    "id": str(server.id),
                    "name": server.name,
                    "endpoint": server.endpoint,
                    "source_ids": server.source_ids,
                    "created_at": server.created_at.isoformat(),
                    "updated_at": server.updated_at.isoformat()
                })
            
            return cors_json_response(servers_data, 200, request)

    # GET /api/v1/mcp-servers/{id} - Get MCP server by ID for user
    @mcp.custom_route("/api/v1/mcp-servers/{server_id}", methods=["GET"])
    async def get_mcp_server(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        server_id = request.path_params.get("server_id")
        
        try:
            server_uuid = uuid.UUID(server_id)
        except ValueError:
            return cors_error_response("Invalid server ID format", 400, request)
        
        # Get user and server with proper session management
        async for db in get_db():
            user_repo = UserRepository(db)
            user = await user_repo.get_by_email(email)
            if not user:
                return cors_error_response("User not found", 401, request)
            
            from repositories.mcp_server_repository import MCPServerRepository
            server_repo = MCPServerRepository(db)
            
            # Check if server belongs to user
            if not await server_repo.server_belongs_to_user(server_uuid, user.id):
                return cors_error_response("MCP server not found", 404, request)
            
            server = await server_repo.get_mcp_server_by_id(server_uuid)
            if not server:
                return cors_error_response("MCP server not found", 404, request)
            
            return cors_json_response({
                "id": str(server.id),
                "name": server.name,
                "endpoint": server.endpoint,
                "source_ids": server.source_ids,
                "created_at": server.created_at.isoformat(),
                "updated_at": server.updated_at.isoformat()
            }, 200, request)

    # POST /api/v1/mcp-servers - Create MCP server for user
    @mcp.custom_route("/api/v1/mcp-servers", methods=["POST"])
    async def create_mcp_server(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        try:
            body = await request.json()
            from schemas.schemas import MCPServerCreate
            
            # Validate basic structure
            server_data = MCPServerCreate(**body)
            
            # Create server with proper session management
            async for db in get_db():
                user_repo = UserRepository(db)
                user = await user_repo.get_by_email(email)
                if not user:
                    return cors_error_response("User not found", 401, request)
                
                # Validate source IDs if provided
                if server_data.source_ids:
                    from repositories.source_repository import SourceRepository
                    source_repo = SourceRepository(db)
                    
                    for source_id_str in server_data.source_ids:
                        try:
                            source_uuid = uuid.UUID(source_id_str)
                        except ValueError:
                            return cors_error_response(f"Invalid source ID format: {source_id_str}", 400, request)
                        
                        # Check if source exists and belongs to user
                        if not await source_repo.source_belongs_to_user(source_uuid, user.id):
                            return cors_error_response(f"Source ID {source_id_str} not found or does not belong to user", 400, request)
                
                from repositories.mcp_server_repository import MCPServerRepository
                server_repo = MCPServerRepository(db)
                
                server = await server_repo.create_mcp_server(
                    user_id=user.id,
                    name=server_data.name,
                    source_ids=server_data.source_ids
                )
                
                if not server:
                    return cors_error_response("No available domains in MCP_GATEWAY_URL_POOLS", 503, request)
                
                await db.commit()
                
                return cors_json_response({
                    "id": str(server.id),
                    "name": server.name,
                    "endpoint": server.endpoint,
                    "source_ids": server.source_ids,
                    "created_at": server.created_at.isoformat(),
                    "updated_at": server.updated_at.isoformat()
                }, 201, request)
            
        except Exception as e:
            return cors_error_response(str(e), 400, request)

    # PUT /api/v1/mcp-servers/{id} - Update MCP server for user
    @mcp.custom_route("/api/v1/mcp-servers/{server_id}", methods=["PUT"])
    async def update_mcp_server(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        server_id = request.path_params.get("server_id")
        
        try:
            server_uuid = uuid.UUID(server_id)
        except ValueError:
            return cors_error_response("Invalid server ID format", 400, request)
        
        try:
            body = await request.json()
            from schemas.schemas import MCPServerUpdate
            from repositories.mcp_server_repository import MCPServerRepository
            
            # Validate update data
            update_data = MCPServerUpdate(**body)
            
            # Update server with proper session management
            async for db in get_db():
                user_repo = UserRepository(db)
                user = await user_repo.get_by_email(email)
                if not user:
                    return cors_error_response("User not found", 401, request)
                
                server_repo = MCPServerRepository(db)
                
                # Check if server belongs to user
                if not await server_repo.server_belongs_to_user(server_uuid, user.id):
                    return cors_error_response("MCP server not found", 404, request)
                
                # Validate source IDs if provided in update
                if update_data.source_ids is not None:
                    from repositories.source_repository import SourceRepository
                    source_repo = SourceRepository(db)
                    
                    for source_id_str in update_data.source_ids:
                        try:
                            source_uuid_check = uuid.UUID(source_id_str)
                        except ValueError:
                            return cors_error_response(f"Invalid source ID format: {source_id_str}", 400, request)
                        
                        # Check if source exists and belongs to user
                        if not await source_repo.source_belongs_to_user(source_uuid_check, user.id):
                            return cors_error_response(f"Source ID {source_id_str} not found or does not belong to user", 400, request)
                
                # Update server
                success = await server_repo.update_mcp_server(
                    server_id=server_uuid,
                    name=update_data.name,
                    source_ids=update_data.source_ids
                )
                
                if not success:
                    return cors_error_response("MCP server not found", 404, request)
                
                await db.commit()
                
                # Return updated server
                updated_server = await server_repo.get_mcp_server_by_id(server_uuid)
                return cors_json_response({
                    "id": str(updated_server.id),
                    "name": updated_server.name,
                    "endpoint": updated_server.endpoint,
                    "source_ids": updated_server.source_ids,
                    "created_at": updated_server.created_at.isoformat(),
                    "updated_at": updated_server.updated_at.isoformat()
                }, 200, request)
            
        except Exception as e:
            return cors_error_response(str(e), 400, request)

    # DELETE /api/v1/mcp-servers/{id} - Delete MCP server for user
    @mcp.custom_route("/api/v1/mcp-servers/{server_id}", methods=["DELETE"])
    async def delete_mcp_server(request: Request):
        email, error_response = await get_current_user_from_request(request)
        if error_response:
            return error_response
        
        server_id = request.path_params.get("server_id")
        
        try:
            server_uuid = uuid.UUID(server_id)
        except ValueError:
            return cors_error_response("Invalid server ID format", 400, request)
        
        # Delete server with proper session management
        async for db in get_db():
            user_repo = UserRepository(db)
            user = await user_repo.get_by_email(email)
            if not user:
                return cors_error_response("User not found", 401, request)
            
            from repositories.mcp_server_repository import MCPServerRepository
            server_repo = MCPServerRepository(db)
            
            # Check if server belongs to user
            if not await server_repo.server_belongs_to_user(server_uuid, user.id):
                return cors_error_response("MCP server not found", 404, request)
            
            # Delete server
            success = await server_repo.delete_mcp_server(server_uuid)
            if not success:
                return cors_error_response("MCP server not found", 404, request)
            
            await db.commit()
            
            return cors_json_response({"message": "MCP server deleted successfully"}, 200, request)

async def get_box_handlers_for_current_domain() -> List[BoxHandler]:
    """
    Extract domain from current request and lookup associated Box sources to create handlers.
    """
    try:
        # Get current URL and extract domain
        current_url = get_http_request().url
        parsed_url = urllib.parse.urlparse(str(current_url))
        domain = parsed_url.netloc
        
        logger.info(f"Looking up Box sources for domain: {domain}")
        
        box_handlers = []
        
        # Query database for MCP servers with this endpoint
        async for db in get_db():
            mcp_server_repo = MCPServerRepository(db)
            source_repo = SourceRepository(db)
            
            # Find MCP servers by endpoint (domain)
            servers = await mcp_server_repo.get_servers_by_endpoint(domain)
            
            for server in servers:
                if server.source_ids:
                    # Get the associated sources
                    sources = await source_repo.get_sources_by_ids(server.source_ids)
                    
                    # Filter for Box sources and create handlers
                    for source in sources:
                        if source.type.lower() == "box" and source.source_metadata:
                            metadata = source.source_metadata
                            
                            # Extract Box credentials from metadata
                            client_id = metadata.get("box_client_id")
                            client_secret = metadata.get("box_client_secret")
                            subject_type = metadata.get("box_subject_type")
                            subject_id = metadata.get("box_subject_id")
                            
                            if all([client_id, client_secret, subject_type, subject_id]):
                                try:
                                    box_handler = BoxHandler(
                                        client_id=client_id,
                                        client_secret=client_secret,
                                        subject_type=subject_type,
                                        subject_id=subject_id
                                    )
                                    box_handlers.append(box_handler)
                                    logger.info(f"Created Box handler for source {source.id}")
                                except Exception as e:
                                    logger.warning(f"Failed to create Box handler for source {source.id}: {e}")
                            else:
                                logger.warning(f"Incomplete Box credentials for source {source.id}")
            
            break  # Only process first database session
        
        logger.info(f"Created {len(box_handlers)} Box handlers for domain {domain}")
        return box_handlers
        
    except Exception as e:
        logger.error(f"Failed to get Box handlers for current domain: {e}")
        return []

async def get_snowflake_handlers_for_current_domain() -> List[SnowflakeCortexHandler]:
    """
    Extract domain from current request and lookup associated Snowflake sources to create handlers.
    """
    try:
        # Get current URL and extract domain
        current_url = get_http_request().url
        parsed_url = urllib.parse.urlparse(str(current_url))
        domain = parsed_url.netloc
        
        logger.info(f"Looking up Snowflake sources for domain: {domain}")
        
        snowflake_handlers = []
        
        # Query database for MCP servers with this endpoint
        async for db in get_db():
            mcp_server_repo = MCPServerRepository(db)
            source_repo = SourceRepository(db)
            
            # Find MCP servers by endpoint (domain)
            servers = await mcp_server_repo.get_servers_by_endpoint(domain)
            
            for server in servers:
                if server.source_ids:
                    # Get the associated sources
                    sources = await source_repo.get_sources_by_ids(server.source_ids)
                    
                    # Filter for Snowflake sources and create handlers
                    for source in sources:
                        if source.type.lower() == "snowflake" and source.source_metadata:
                            metadata = source.source_metadata
                            
                            # Extract Snowflake credentials from metadata
                            semantic_model_file = metadata.get("snowflake_semantic_model_file")
                            cortex_search_service = metadata.get("snowflake_cortex_search_service")
                            snowflake_account_url = metadata.get("snowflake_account_url")
                            snowflake_pat = metadata.get("snowflake_pat")
                            
                            if all([semantic_model_file, cortex_search_service, snowflake_account_url, snowflake_pat]):
                                try:
                                    snowflake_handler = SnowflakeCortexHandler(
                                        semantic_model_file=semantic_model_file,
                                        cortex_search_service=cortex_search_service,
                                        snowflake_account_url=snowflake_account_url,
                                        snowflake_pat=snowflake_pat
                                    )
                                    snowflake_handlers.append(snowflake_handler)
                                    logger.info(f"Created Snowflake handler for source {source.id}")
                                except Exception as e:
                                    logger.warning(f"Failed to create Snowflake handler for source {source.id}: {e}")
                            else:
                                logger.warning(f"Incomplete Snowflake credentials for source {source.id}")
            
            break  # Only process first database session
        
        logger.info(f"Created {len(snowflake_handlers)} Snowflake handlers for domain {domain}")
        return snowflake_handlers
        
    except Exception as e:
        logger.error(f"Failed to get Snowflake handlers for current domain: {e}")
        return []

async def get_outlook_handlers_for_current_domain() -> List[OutlookHandler]:
    """
    Extract domain from current request and lookup associated Outlook sources to create handlers.
    """
    try:
        # Get current URL and extract domain
        current_url = get_http_request().url
        parsed_url = urllib.parse.urlparse(str(current_url))
        domain = parsed_url.netloc
        
        logger.info(f"Looking up Outlook sources for domain: {domain}")
        
        outlook_handlers = []
        
        # Query database for MCP servers with this endpoint
        async for db in get_db():
            mcp_server_repo = MCPServerRepository(db)
            source_repo = SourceRepository(db)
            
            # Find MCP servers by endpoint (domain)
            servers = await mcp_server_repo.get_servers_by_endpoint(domain)
            
            for server in servers:
                if server.source_ids:
                    # Get the associated sources
                    sources = await source_repo.get_sources_by_ids(server.source_ids)
                    
                    # Filter for Outlook sources and create handlers
                    for source in sources:
                        if source.type.lower() == "outlook" and source.source_metadata:
                            metadata = source.source_metadata
                            
                            # Extract Outlook credentials from metadata
                            tenant_id = metadata.get("tenant_id")
                            client_id = metadata.get("graph_client_id")
                            client_secret = metadata.get("graph_client_secret")
                            user_id = metadata.get("graph_user_id")
                            scope = "https://graph.microsoft.com/.default"
                            
                            if all([tenant_id, client_id, client_secret, user_id]):
                                try:
                                    outlook_handler = OutlookHandler(
                                        tenant_id=tenant_id,
                                        client_id=client_id,
                                        client_secret=client_secret,
                                        user_id=user_id,
                                        scope=scope
                                    )
                                    outlook_handlers.append(outlook_handler)
                                    logger.info(f"Created Outlook handler for source {source.id}")
                                except Exception as e:
                                    logger.warning(f"Failed to create Outlook handler for source {source.id}: {e}")
                            else:
                                logger.warning(f"Incomplete Outlook credentials for source {source.id}")
            
            break  # Only process first database session
        
        logger.info(f"Created {len(outlook_handlers)} Outlook handlers for domain {domain}")
        return outlook_handlers
        
    except Exception as e:
        logger.error(f"Failed to get Outlook handlers for current domain: {e}")
        return []

def create_server() -> FastMCP:
    mcp = FastMCP(name="Modular MCP Server", instructions=SERVER_INSTRUCTIONS)

    # Register authentication routes
    register_auth_routes(mcp)

    @mcp.tool()
    async def search(query: str, ctx: Context) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregated search across all registered handlers.
        Returns: {"results": [{"id","title","text","url"}]}
        """
        print("search get_http_request().url", get_http_request().url)

        # Get dynamic handlers
        box_handlers = await get_box_handlers_for_current_domain()
        snowflake_handlers = await get_snowflake_handlers_for_current_domain()
        outlook_handlers = await get_outlook_handlers_for_current_domain()
        
        # Combine all dynamic handlers
        all_handlers = [
            *box_handlers,       # Dynamic Box handlers
            *snowflake_handlers, # Dynamic Snowflake handlers
            *outlook_handlers,   # Dynamic Outlook handlers
        ]

        all_results: List[Dict[str, Any]] = []
        for h in all_handlers:
            try:
                results = await h.search(query=query, top=10)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"[SEARCH] handler={h.name} failed: {e}")
        logger.info(f"[SEARCH] total results={len(all_results)}")
        return {"results": all_results}

    @mcp.tool()
    async def fetch(id: str, ctx: Context) -> Dict[str, Any]:
        """
        Routed fetch based on id prefix:
        - 'outlook::xxxx' -> Outlook handler
        """
        print("fetch get_http_request().url", get_http_request().url)
        if not id or "::" not in id:
            raise ValueError("id must be in the form '<prefix>::<native_id>'")
        prefix, native_id = id.split("::", 1)
        
        # Get dynamic handlers and create complete handler mapping
        box_handlers = await get_box_handlers_for_current_domain()
        snowflake_handlers = await get_snowflake_handlers_for_current_domain()
        outlook_handlers = await get_outlook_handlers_for_current_domain()
        
        all_handlers = [
            *box_handlers,
            *snowflake_handlers,
            *outlook_handlers,
        ]
        complete_handler_by_prefix = {h.id_prefix: h for h in all_handlers}
        
        handler = complete_handler_by_prefix.get(prefix)
        if not handler:
            raise ValueError(f"No handler registered for prefix '{prefix}::'")
        try:
            return await handler.fetch(native_id)
        except Exception as e:
            logger.error(f"[FETCH] handler={handler.name} failed: {e}")
            raise
    
    # ---- Health endpoint at /checks ----
    @mcp.custom_route("/api/v1/checks", methods=["GET"])
    async def health_check(request: Request):
        # Optionally: add lightweight dependency probes here
        # ok = await handlers[0].ping()  # if your handler exposes a ping
        uptime = time.time() - START_TIME
        
        # Get count of dynamic handlers
        box_handlers = await get_box_handlers_for_current_domain()
        snowflake_handlers = await get_snowflake_handlers_for_current_domain()
        outlook_handlers = await get_outlook_handlers_for_current_domain()
        
        return cors_json_response({
            "status": "healthy",
            "service": "modular-mcp-server",
            "uptime_seconds": round(uptime, 2),
            "dynamic_handlers": {
                "box": len(box_handlers),
                "snowflake": len(snowflake_handlers),
                "outlook": len(outlook_handlers)
            }
        }, 200, request)

    # ---- Fallback route for all other requests ----
    @mcp.custom_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
    async def fallback_route(request: Request):
        """Fallback route that catches all other requests and logs details"""
        method = request.method
        url = str(request.url)
        headers = dict(request.headers)
        
        # Try to read request body if present
        body = None
        try:
            body_bytes = await request.body()
            if body_bytes:
                try:
                    body = body_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    body = f"<binary data: {len(body_bytes)} bytes>"
        except Exception as e:
            body = f"<error reading body: {e}>"
        
        # Log the request details
        logger.info(f"[FALLBACK] {method} {url}")
        logger.info(f"[FALLBACK] Headers: {headers}")
        if body:
            logger.info(f"[FALLBACK] Body: {body}")
        
        return cors_json_response({
            "message": "Endpoint not found",
            "method": method,
            "url": url,
            "headers": headers,
            "body": body
        }, 404, request)

    return mcp

def main():
    server = create_server()
    logger.info("Starting MCP server on 0.0.0.0:8000 (SSE)")
    try:
        # Run with HTTP transport which supports both REST APIs and MCP
        server.run(transport="sse", host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    main()
