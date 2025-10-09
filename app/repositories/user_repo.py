from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from .base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(sa.func.lower(User.email) == sa.func.lower(sa.literal(email)))
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def create(self, *, name: str, email: str, hashed_password: str, campus: str | None = None) -> User:
        user = User(name=name, email=email, hashed_password=hashed_password, campus=campus)
        return await self.add(user)
