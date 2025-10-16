import uuid
import os
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from database.models import MCPServer


class MCPServerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_available_domains(self) -> List[str]:
        """Get list of available domains from environment variable."""
        domain_pools = os.getenv('MCP_GATEWAY_URL_POOLS', '')
        if not domain_pools:
            return []
        return [domain.strip() for domain in domain_pools.split(',') if domain.strip()]

    async def _get_used_domains(self) -> List[str]:
        """Get list of already used domains (including soft-deleted ones)."""
        query = select(MCPServer.endpoint)
        result = await self.db.execute(query)
        return [endpoint for endpoint in result.scalars().all()]

    async def _get_next_available_domain(self) -> Optional[str]:
        """Get the next available domain from the pool."""
        available_domains = self._get_available_domains()
        used_domains = await self._get_used_domains()
        
        for domain in available_domains:
            if domain not in used_domains:
                return domain
        
        return None

    async def create_mcp_server(
        self, 
        user_id: uuid.UUID, 
        name: str,
        source_ids: Optional[List[str]] = None
    ) -> Optional[MCPServer]:
        """Create a new MCP server using an available domain from the pool."""
        # Get next available domain from the pool
        endpoint = await self._get_next_available_domain()
        if not endpoint:
            return None  # No available domains
        
        mcp_server = MCPServer(
            user_id=user_id,
            name=name,
            endpoint=endpoint,
            source_ids=source_ids or []
        )
        self.db.add(mcp_server)
        await self.db.flush()
        return mcp_server

    async def get_mcp_server_by_id(self, server_id: uuid.UUID) -> Optional[MCPServer]:
        """Get MCP server by ID (excluding soft-deleted)."""
        query = select(MCPServer).where(
            MCPServer.id == server_id,
            MCPServer.deleted_at.is_(None)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_user_mcp_servers(self, user_id: uuid.UUID) -> List[MCPServer]:
        """Get all MCP servers for a user (excluding soft-deleted)."""
        query = select(MCPServer).where(
            MCPServer.user_id == user_id,
            MCPServer.deleted_at.is_(None)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_mcp_server(
        self, 
        server_id: uuid.UUID, 
        name: Optional[str] = None,
        source_ids: Optional[List[str]] = None
    ) -> bool:
        """Update MCP server (endpoint cannot be updated)."""
        values = {}
        if name is not None:
            values['name'] = name
        if source_ids is not None:
            values['source_ids'] = source_ids
        
        if not values:
            return False
            
        query = update(MCPServer).where(
            MCPServer.id == server_id,
            MCPServer.deleted_at.is_(None)
        ).values(**values)
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def delete_mcp_server(self, server_id: uuid.UUID) -> bool:
        """Soft delete MCP server."""
        query = update(MCPServer).where(
            MCPServer.id == server_id,
            MCPServer.deleted_at.is_(None)
        ).values(deleted_at=datetime.utcnow())
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def add_source_to_server(self, server_id: uuid.UUID, source_id: str) -> bool:
        """Add a source to an MCP server (only non-deleted servers)."""
        server = await self.get_mcp_server_by_id(server_id)
        if not server:
            return False
        
        if source_id not in server.source_ids:
            server.source_ids.append(source_id)
            await self.db.flush()
        
        return True

    async def remove_source_from_server(self, server_id: uuid.UUID, source_id: str) -> bool:
        """Remove a source from an MCP server (only non-deleted servers)."""
        server = await self.get_mcp_server_by_id(server_id)
        if not server:
            return False
        
        if source_id in server.source_ids:
            server.source_ids.remove(source_id)
            await self.db.flush()
        
        return True

    async def server_belongs_to_user(self, server_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check if MCP server belongs to user (only non-deleted servers)."""
        query = select(MCPServer).where(
            MCPServer.id == server_id, 
            MCPServer.user_id == user_id,
            MCPServer.deleted_at.is_(None)
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def get_servers_with_source(self, user_id: uuid.UUID, source_id: str) -> List[MCPServer]:
        """Get all servers that include a specific source (only non-deleted servers)."""
        query = select(MCPServer).where(
            MCPServer.user_id == user_id,
            MCPServer.source_ids.any(source_id),
            MCPServer.deleted_at.is_(None)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_servers_by_endpoint(self, endpoint: str) -> List[MCPServer]:
        """Get all MCP servers by endpoint (including soft-deleted for domain management)."""
        query = select(MCPServer).where(MCPServer.endpoint == endpoint)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def hard_delete_mcp_server(self, server_id: uuid.UUID) -> bool:
        """Permanently delete MCP server (for admin use)."""
        query = delete(MCPServer).where(MCPServer.id == server_id)
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def restore_mcp_server(self, server_id: uuid.UUID) -> bool:
        """Restore a soft-deleted MCP server."""
        query = update(MCPServer).where(
            MCPServer.id == server_id,
            MCPServer.deleted_at.is_not(None)
        ).values(deleted_at=None)
        result = await self.db.execute(query)
        return result.rowcount > 0
