from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repo import UserRepository
from app.models.user import User

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACCESS_MIN = int(os.getenv("JWT_ACCESS_MIN", "30"))
REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "30"))

def hash_password(raw: str) -> str:
    return _pwd_ctx.hash(raw)

def verify_password(raw: str, hashed: str) -> bool:
    return _pwd_ctx.verify(raw, hashed)

def _encode(payload: Dict[str, Any], expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    data = {"iat": int(now.timestamp()), "exp": int((now + expires_delta).timestamp()), **payload}
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALG)

def make_token_pair(user: User) -> dict:
    access = _encode({"sub": user.id, "typ": "access"}, timedelta(minutes=ACCESS_MIN))
    refresh = _encode({"sub": user.id, "typ": "refresh"}, timedelta(days=REFRESH_DAYS))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

async def register_user(db: AsyncSession, *, name: str, email: str, password: str, campus: str | None) -> User:
    repo = UserRepository(db)
    existing = await repo.get_by_email(email)
    if existing:
        raise ValueError("email already registered")
    user = await repo.create(name=name, email=email, hashed_password=hash_password(password), campus=campus)
    await db.commit()
    return user

async def authenticate_user(db: AsyncSession, *, email: str, password: str) -> Optional[User]:
    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
