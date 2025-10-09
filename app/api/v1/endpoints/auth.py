from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import RegisterIn, LoginIn, TokenPair, RefreshIn
from app.schemas.user import UserOut
from app.services.auth_service import authenticate_user, make_token_pair, register_user, decode_token
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=201)
async def register(data: RegisterIn, db: AsyncSession = Depends(get_db)):
    try:
        user = await register_user(db, name=data.name, email=data.email, password=data.password, campus=data.campus)
        return UserOut.model_validate(user, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenPair)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, email=data.email, password=data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    tokens = make_token_pair(user)
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    return tokens

@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshIn, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("typ") != "refresh":
            raise ValueError("invalid token typ")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("missing sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return make_token_pair(user)

@router.get("/me", response_model=UserOut)
async def me(current=Depends(get_current_user)):
    return UserOut.model_validate(current)
