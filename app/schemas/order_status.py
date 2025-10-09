from __future__ import annotations
from datetime import datetime
from app.schemas.common import ORMModel, IdOut

class OrderStatusHistoryOut(ORMModel, IdOut):
    order_id: str
    from_status: str | None
    to_status: str
    reason: str | None
    created_at: datetime
