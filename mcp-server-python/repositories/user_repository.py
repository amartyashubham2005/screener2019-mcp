import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError

from database.models import User
from auth.utils import AuthUtils


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, email: str, password: str) -> Optional[User]:
        """Create a new user."""
        try:
            hashed_password = AuthUtils.hash_password(password)
            user = User(
                email=email,
                hashed_password=hashed_password
            )
            self.db.add(user)
            await self.db.flush()
            return user
        except IntegrityError:
            await self.db.rollback()
            return None  # User already exists

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Alias for get_user_by_email."""
        return await self.get_user_by_email(email)
    
    async def create(self, user_data: dict) -> User:
        """Create a new user from dict data."""
        user = User(**user_data)
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not AuthUtils.verify_password(password, user.hashed_password):
            return None
        return user

    async def update_user_password(self, user_id: uuid.UUID, new_password: str) -> bool:
        """Update user password."""
        hashed_password = AuthUtils.hash_password(new_password)
        query = update(User).where(User.id == user_id).values(hashed_password=hashed_password)
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete user and all associated data."""
        query = delete(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination."""
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
