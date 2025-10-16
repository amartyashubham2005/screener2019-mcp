import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# User schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=8)


# Source metadata schemas
class OutlookMetadata(BaseModel):
    tenant_id: str
    graph_client_id: str
    graph_client_secret: str
    graph_user_id: str


class SnowflakeMetadata(BaseModel):
    snowflake_account_url: str
    snowflake_pat: str
    snowflake_semantic_model_file: str
    snowflake_cortex_search_service: str


class BoxMetadata(BaseModel):
    box_client_id: str
    box_client_secret: str
    box_subject_type: str
    box_subject_id: str


# Source schemas
class SourceBase(BaseModel):
    type: str = Field(..., pattern="^(outlook|box|snowflake)$")
    source_metadata: Dict[str, Any]


class SourceCreate(SourceBase):
    pass


class Source(SourceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SourceUpdate(BaseModel):
    type: Optional[str] = Field(None, pattern="^(outlook|box|snowflake)$")
    source_metadata: Optional[Dict[str, Any]] = None


# MCP Server schemas
class MCPServerBase(BaseModel):
    name: str = Field(..., max_length=255)
    source_ids: Optional[List[str]] = Field(default_factory=list)


class MCPServerCreate(MCPServerBase):
    pass


class MCPServer(MCPServerBase):
    id: uuid.UUID
    user_id: uuid.UUID
    endpoint: str = Field(..., max_length=500)
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MCPServerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    source_ids: Optional[List[str]] = None


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    user_id: Optional[uuid.UUID] = None
    email: Optional[str] = None
