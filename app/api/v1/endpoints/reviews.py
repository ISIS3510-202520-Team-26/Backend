from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.review import ReviewCreate, ReviewOut

from app.api.deps import get_db, get_current_user
from app.repositories.review_repo import ReviewRepository

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    repo = ReviewRepository(db)
    rec = await repo.create(
        order_id=body.order_id,
        rater_id=user.id,
        ratee_id=body.ratee_id,
        rating=body.rating,
        comment=body.comment,
    )
    await db.commit()
    return ReviewOut(
        id=rec.id,
        order_id=rec.order_id,
        rater_id=rec.rater_id,
        ratee_id=rec.ratee_id,
        rating=rec.rating,
        comment=rec.comment,
        created_at=rec.created_at,
    )

@router.get("/users/{user_id}", response_model=list[ReviewOut])
async def list_for_user(user_id: str, db: AsyncSession = Depends(get_db)):
    repo = ReviewRepository(db)
    rows = await repo.list_for_user(user_id, limit=50)
    return [
        ReviewOut(
            id=r.id,
            order_id=r.order_id,
            rater_id=r.rater_id,
            ratee_id=r.ratee_id,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in rows
    ]

@router.get("/orders/{order_id}", response_model=ReviewOut | None)
async def get_by_order(order_id: str, db: AsyncSession = Depends(get_db)):
    repo = ReviewRepository(db)
    r = await repo.get_by_order(order_id)
    if not r:
        return None
    return ReviewOut(
        id=r.id,
        order_id=r.order_id,
        rater_id=r.rater_id,
        ratee_id=r.ratee_id,
        rating=r.rating,
        comment=r.comment,
        created_at=r.created_at,
    )
