from __future__ import annotations
from typing import Any, Generic, Iterable, TypeVar, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import InstrumentedAttribute
from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)

class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    async def get(self, id_: str) -> ModelT | None:
        return await self.session.get(self.model, id_)

    async def list(
        self,
        where: Iterable[Any] | None = None,
        order_by: Iterable[InstrumentedAttribute] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[ModelT]:
        stmt = select(self.model)
        if where:
            for cond in where:
                stmt = stmt.where(cond)
        if order_by:
            stmt = stmt.order_by(*order_by)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def count(self, where: Iterable[Any] | None = None) -> int:
        stmt = select(self.model)
        if where:
            for cond in where:
                stmt = stmt.where(cond)
        subq = stmt.subquery()
        res = await self.session.execute(select(func.count()).select_from(subq))
        return int(res.scalar_one())

    async def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.flush() 
        return obj

    async def delete(self, id_: str) -> int:
        stmt = delete(self.model).where(self.model.id == id_).execution_options(synchronize_session=False)
        res = await self.session.execute(stmt)
        return res.rowcount or 0

from sqlalchemy import func  
