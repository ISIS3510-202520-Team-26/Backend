from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.escrow import Escrow, EscrowEvent
from app.models.enums import EscrowStatus
from .base import BaseRepository

class EscrowRepository(BaseRepository[Escrow]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Escrow)

    async def create_for_order(self, *, order_id: str, provider: str, status: EscrowStatus) -> Escrow:
        escrow = Escrow(order_id=order_id, provider=provider, status=status)
        return await self.add(escrow)

    async def add_event(self, *, escrow_id: str, step: str, result: str | None) -> EscrowEvent:
        ev = EscrowEvent(escrow_id=escrow_id, step=step, result=result)
        self.session.add(ev)
        await self.session.flush()
        return ev

    async def set_status(self, escrow: Escrow, status: EscrowStatus) -> Escrow:
        escrow.status = status
        await self.session.flush()
        return escrow
