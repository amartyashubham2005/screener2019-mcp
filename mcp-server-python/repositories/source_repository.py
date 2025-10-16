import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from database.models import Source


class SourceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_source(
        self, 
        user_id: uuid.UUID, 
        source_type: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Source:
        """Create a new source."""
        source = Source(
            user_id=user_id,
            type=source_type,
            source_metadata=metadata or {}
        )
        self.db.add(source)
        await self.db.flush()
        return source

    async def get_source_by_id(self, source_id: uuid.UUID) -> Optional[Source]:
        """Get source by ID."""
        query = select(Source).where(Source.id == source_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_user_sources(self, user_id: uuid.UUID) -> List[Source]:
        """Get all sources for a user."""
        query = select(Source).where(Source.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_source(
        self, 
        source_id: uuid.UUID, 
        source_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update source."""
        values = {}
        if source_type is not None:
            values['type'] = source_type
        if metadata is not None:
            values['source_metadata'] = metadata
        
        if not values:
            return False
            
        query = update(Source).where(Source.id == source_id).values(**values)
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def delete_source(self, source_id: uuid.UUID) -> bool:
        """Delete source."""
        query = delete(Source).where(Source.id == source_id)
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def get_sources_by_type(self, user_id: uuid.UUID, source_type: str) -> List[Source]:
        """Get user sources by type."""
        query = select(Source).where(Source.user_id == user_id, Source.type == source_type)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def source_belongs_to_user(self, source_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check if source belongs to user."""
        query = select(Source).where(Source.id == source_id, Source.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def get_sources_by_ids(self, source_ids: List[str]) -> List[Source]:
        """Get sources by list of IDs."""
        # Convert string IDs to UUIDs
        uuid_ids = []
        for source_id in source_ids:
            try:
                uuid_ids.append(uuid.UUID(source_id))
            except ValueError:
                continue  # Skip invalid UUIDs
        
        if not uuid_ids:
            return []
            
        query = select(Source).where(Source.id.in_(uuid_ids))
        result = await self.db.execute(query)
        return result.scalars().all()
