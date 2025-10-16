# MCP Server Database Setup

This document describes the database setup and migration process for the MCP server with user authentication and CRUD operations.

## Database Schema

The database consists of three main tables:

### Users Table
- `id` (UUID, Primary Key) - Auto-generated UUIDv4
- `email` (String, Unique) - User's email address
- `hashed_password` (String) - Bcrypt hashed password
- `created_at` (Timestamp) - Auto-populated on creation
- `updated_at` (Timestamp) - Auto-updated on modification

### Sources Table
- `id` (UUID, Primary Key) - Auto-generated UUIDv4
- `type` (String) - Type of the data source (e.g., "outlook", "box", "snowflake")
- `source_metadata` (JSONB) - Flexible metadata storage for source configuration
- `user_id` (UUID, Foreign Key) - References users.id with CASCADE delete
- `created_at` (Timestamp) - Auto-populated on creation
- `updated_at` (Timestamp) - Auto-updated on modification

### MCP Servers Table
- `id` (UUID, Primary Key) - Auto-generated UUIDv4
- `name` (String) - Human-readable name for the MCP server
- `endpoint` (String) - URL/endpoint for the MCP server (auto-assigned from pool)
- `source_ids` (Array<String>) - List of source IDs that this server has access to
- `user_id` (UUID, Foreign Key) - References users.id with CASCADE delete
- `created_at` (Timestamp) - Auto-populated on creation
- `updated_at` (Timestamp) - Auto-updated on modification
- `deleted_at` (Timestamp, Nullable) - Soft deletion timestamp

## Environment Variables

Make sure your `.env` file contains:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/mcp_server

# JWT Configuration
JWT_SECRET_KEY=your-super-secure-secret-key-change-in-production

# MCP Gateway URL Pool Configuration
MCP_GATEWAY_URL_POOLS=https://mcp1.example.com,https://mcp2.example.com,https://mcp3.example.com
```

**Note**: `MCP_GATEWAY_URL_POOLS` is a comma-separated list of domain URLs that can be used for MCP servers. Each MCP server created will be assigned one of these domains automatically. The number of available domains limits the maximum number of MCP servers that can be created.

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL Database**:
   - Install PostgreSQL if not already installed
   - Create a database named `mcp_server` (or use your preferred name)
   - Update the `DATABASE_URL` in your `.env` file

3. **Run Database Setup**:
   ```bash
   python setup_db.py
   ```

4. **Alternative: Use Alembic Migrations**:
   ```bash
   # Run migrations (when database is running)
   alembic upgrade head
   ```

## Features Implemented

### Authentication System
- **Password Hashing**: Uses bcrypt for secure password hashing
- **JWT Tokens**: JSON Web Tokens for session management
- **User Registration**: Email/password based registration with validation
- **User Login**: Authentication with email and password

### Database Repositories
- **UserRepository**: CRUD operations for users with authentication methods
- **SourceRepository**: CRUD operations for data sources with user isolation
- **MCPServerRepository**: CRUD operations for MCP servers with source management

### Data Models
- **Async SQLAlchemy**: Modern async database operations
- **UUID Primary Keys**: All tables use UUIDv4 as primary keys
- **Automatic Timestamps**: Created/updated timestamps with database triggers
- **Foreign Key Constraints**: Proper relationships with cascade delete
- **Data Validation**: Pydantic schemas for API serialization/validation

### Security Features
- **User Isolation**: All resources are isolated by user_id
- **Password Security**: Bcrypt hashing with salt
- **JWT Security**: Configurable secret keys and expiration
- **Input Validation**: Comprehensive validation using Pydantic

## Repository Methods

### UserRepository
- `create_user(email, password)` - Register new user
- `authenticate_user(email, password)` - Login authentication
- `get_user_by_id(user_id)` - Get user by ID
- `get_user_by_email(email)` - Get user by email
- `update_user_password(user_id, new_password)` - Change password
- `delete_user(user_id)` - Delete user and all associated data

### SourceRepository
- `create_source(user_id, type, metadata)` - Create new data source
- `get_user_sources(user_id)` - Get all sources for a user
- `get_source_by_id(source_id)` - Get specific source
- `update_source(source_id, type, metadata)` - Update source
- `delete_source(source_id)` - Delete source
- `source_belongs_to_user(source_id, user_id)` - Ownership check

### MCPServerRepository
- `create_mcp_server(user_id, name, source_ids)` - Create MCP server (endpoint auto-assigned from pool)
- `get_user_mcp_servers(user_id)` - Get all servers for a user (excluding soft-deleted)
- `get_mcp_server_by_id(server_id)` - Get specific server (excluding soft-deleted)
- `update_mcp_server(server_id, name, source_ids)` - Update server (endpoint cannot be updated)
- `delete_mcp_server(server_id)` - Soft delete server (sets deleted_at timestamp)
- `add_source_to_server(server_id, source_id)` - Add source to server
- `remove_source_from_server(server_id, source_id)` - Remove source from server
- `hard_delete_mcp_server(server_id)` - Permanently delete server (admin use)
- `restore_mcp_server(server_id)` - Restore soft-deleted server

## Next Steps

The database layer is now ready. The next phase will involve:

1. **REST API Endpoints**: Create FastAPI routes for all CRUD operations
2. **Authentication Middleware**: JWT token validation for protected routes
3. **API Documentation**: Automatic OpenAPI/Swagger documentation
4. **Integration**: Connect with existing MCP handlers
5. **Testing**: Unit and integration tests for all components

## Database Migration Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Check current migration status
alembic current

# View migration history
alembic history
```
