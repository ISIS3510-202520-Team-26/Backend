from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.repositories.brand_repo import BrandRepository
from app.schemas.brand import BrandCreate, BrandOut

router = APIRouter(prefix="/brands", tags=["brands"])

@router.post("", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
async def create_brand(data: BrandCreate, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    repo = BrandRepository(db)
    obj = await repo.create(name=data.name, slug=data.slug, category_id=data.category_id)
    await db.commit()
    return BrandOut.model_validate(obj)

@router.get("", response_model=list[BrandOut])
async def list_brands(category_id: str | None = None, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    repo = BrandRepository(db)
    if category_id:
        items = await repo.list_by_category(category_id)
    else:
        items = await repo.list(order_by=[])
    return [BrandOut.model_validate(b) for b in items]
