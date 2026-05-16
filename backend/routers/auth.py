"""Auth router — registration and login endpoints (active only when AUTH_ENABLED=true)."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import get_password_hash, verify_password, create_access_token
from models.database import get_db
from models.orm_models import User as UserORM
from models.schemas import (
    AuthRegisterRequest,
    AuthRegisterResponse,
    AuthLoginRequest,
    AuthLoginResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=AuthRegisterResponse)
async def register(request: AuthRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication is disabled. Set AUTH_ENABLED=true to enable.",
        )

    # Check if username already exists
    result = await db.execute(select(UserORM).where(UserORM.username == request.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists.",
        )

    user = UserORM(
        username=request.username,
        hashed_password=get_password_hash(request.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return AuthRegisterResponse(
        user_id=user.id,
        username=user.username,
        created_at=user.created_at,
    )


@router.post("/login", response_model=AuthLoginResponse)
async def login(request: AuthLoginRequest, db: AsyncSession = Depends(get_db)):
    """Login and receive JWT token."""
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication is disabled. Set AUTH_ENABLED=true to enable.",
        )

    result = await db.execute(select(UserORM).where(UserORM.username == request.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return AuthLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )
