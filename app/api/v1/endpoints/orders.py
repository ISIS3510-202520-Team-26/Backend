from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.repositories.listing_repo import ListingRepository
from app.repositories.order_repo import OrderRepository
from app.schemas.order import OrderCreate, OrderOut
from app.services.order_service import pay_order, cancel_order, complete_order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_new_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current=Depends(get_current_user),
):
    # 1) Validar listing
    listing_repo = ListingRepository(db)
    listing = await listing_repo.get(str(data.listing_id))
    if not listing or not getattr(listing, "is_active", True):
        raise HTTPException(status_code=404, detail="Listing not found or inactive")

    if str(listing.seller_id) == str(current.id):
        raise HTTPException(status_code=400, detail="You cannot buy your own listing")

    qty = int(data.quantity or 1)
    base_total = int(getattr(listing, "price_cents", 0)) * qty
    total_cents = int(data.total_cents) if data.total_cents is not None else base_total
    currency = (data.currency or getattr(listing, "currency", None) or "COP").upper()

    order_repo = OrderRepository(db)
    created = await order_repo.create(
        buyer_id=str(current.id),
        seller_id=str(listing.seller_id),
        listing_id=str(listing.id),
        total_cents=total_cents,
        currency=currency,
    )
    await db.flush()
    await db.commit()

    order_id = str(getattr(created, "id", created)) 
    order_db = await order_repo.get(order_id)
    if not order_db:
        raise HTTPException(status_code=500, detail="Order not found after creation")
    return OrderOut.model_validate(order_db, from_attributes=True)


@router.post("/{order_id}/pay", response_model=OrderOut, status_code=status.HTTP_202_ACCEPTED)
async def pay(order_id: str, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    ok = await pay_order(db, order_id=order_id)
    await db.commit()
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot pay order")

    repo = OrderRepository(db)
    obj = await repo.get_with_relations(order_id) or await repo.get(order_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderOut.model_validate(obj, from_attributes=True)


@router.post("/{order_id}/complete", response_model=OrderOut, status_code=status.HTTP_200_OK)
async def complete(order_id: str, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    ok = await complete_order(db, order_id=order_id)
    await db.commit()
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot complete order")

    repo = OrderRepository(db)
    obj = await repo.get_with_relations(order_id) or await repo.get(order_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderOut.model_validate(obj, from_attributes=True)


@router.post("/{order_id}/cancel", response_model=OrderOut, status_code=status.HTTP_200_OK)
async def cancel(order_id: str, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    ok = await cancel_order(db, order_id=order_id, reason="cancelled_by_user")
    await db.commit()
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot cancel order")

    repo = OrderRepository(db)
    obj = await repo.get_with_relations(order_id) or await repo.get(order_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderOut.model_validate(obj, from_attributes=True)
