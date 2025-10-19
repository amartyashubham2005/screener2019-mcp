import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, Text, ForeignKey, ARRAY, BigInteger, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from .config import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Azure AD fields
    azure_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    azure_tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="local", server_default="local")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    sources: Mapped[List["Source"]] = relationship(
        "Source", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    mcp_servers: Mapped[List["MCPServer"]] = relationship(
        "MCPServer", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )


class Source(Base):
    __tablename__ = "sources"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sources")


class MCPServer(Base):
    __tablename__ = "mcp_servers"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    source_ids: Mapped[List[str]] = mapped_column(
        ARRAY(String), 
        nullable=True,
        default=[]
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mcp_servers")


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    ts: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    operation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    elapsed_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    log_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
    source: Mapped[Optional["Source"]] = relationship("Source")
