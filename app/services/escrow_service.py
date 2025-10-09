from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import EscrowStatus
from app.repositories.escrow_repo import EscrowRepository
from app.repositories.events_repo import EventRepository  
from typing import Optional

async def create_escrow(db: AsyncSession, *, order_id: str, provider: str = "mock") -> str:
    er = EscrowRepository(db)
    e = await er.create_for_order(order_id=order_id, provider=provider, status=EscrowStatus.initiated)
    await er.add_event(escrow_id=e.id, step="listing_viewed", result="success")  
    await db.flush()
    return e.id

async def set_status(db: AsyncSession, *, escrow_id: str, status: EscrowStatus, step: Optional[str] = None, result: Optional[str] = None) -> None:
    er = EscrowRepository(db)
    e = await er.get(escrow_id)
    if not e:
        return
    await er.set_status(e, status)
    if step:
        await er.add_event(escrow_id=escrow_id, step=step, result=result)
    await db.flush()

async def emit_escrow_step_event(db: AsyncSession, *, escrow_id: str, step: str, result: str) -> None:
    escrows = EscrowRepository(db)
    e = await escrows.get(escrow_id)
    if not e:
        return
    await escrows.add_event(escrow_id=escrow_id, step=step, result=result)
    repo = EventRepository(db)
    await repo.insert_batch([{
        "event_type": "escrow.step",
        "session_id": "srv",  
        "user_id": None,
        "order_id": e.order_id,
        "step": step,
        "properties": {},
    }])
    await db.flush()
