from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_db
from repositories.user_repository import UserRepository
from schemas.schemas import UserCreate, UserLogin, User, Token
from auth.utils import AuthUtils

router = APIRouter(prefix="/api/v1", tags=["authentication"])
security = HTTPBearer()


@router.post("/signup", response_model=User)
async def signup(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    user_repo = UserRepository(db)
    
    # Check if user already exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = AuthUtils.hash_password(user_data.password)
    user = await user_repo.create({
        "email": user_data.email,
        "hashed_password": hashed_password
    })
    
    return User(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/signin", response_model=Token)
async def signin(
    user_data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token."""
    user_repo = UserRepository(db)
    
    # Get user by email
    user = await user_repo.get_by_email(user_data.email)
    if not user or not AuthUtils.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = AuthUtils.create_access_token(user.email)
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=24 * 60 * 60  # 24 hours
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/signout")
async def signout(response: Response):
    """Sign out user by clearing the authentication cookie."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="strict"
    )
    return {"message": "Successfully signed out"}


@router.get("/me", response_model=User)
async def get_current_user(request: Request):
    """Get current authenticated user information."""
    # User is set by AuthMiddleware
    user = request.state.current_user
    
    return User(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
