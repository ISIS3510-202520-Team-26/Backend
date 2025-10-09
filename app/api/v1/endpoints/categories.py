from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.repositories.category_repo import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    repo = CategoryRepository(db)
    obj = await repo.create(slug=data.slug, name=data.name)
    await db.commit()
    return CategoryOut.model_validate(obj)

@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    repo = CategoryRepository(db)
    items = await repo.list(order_by=[])
    return [CategoryOut.model_validate(c) for c in items]
