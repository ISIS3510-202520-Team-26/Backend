from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from app.api.deps import get_current_user  # si quieres restringir a admin, aquí puedes verificar roles

# Celery
from celery.result import AsyncResult
from app.workers.celery_app import celery_app
from app.workers.jobs.thumbnails import generate_thumbnail_task
from app.workers.jobs.price_precompute import precompute_recent_prices
from app.workers.jobs.cleanup import cleanup_orphan_objects

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

class TaskOut(BaseModel):
    task_id: str

class TaskStatusOut(BaseModel):
    task_id: str
    state: str
    result: dict | None = None


@router.post("/thumbnails/rebuild", response_model=TaskOut, status_code=status.HTTP_202_ACCEPTED)
async def thumbnails_rebuild(
    object_key: str,
    sizes: list[int] = Query(default=[300, 800]),
    current=Depends(get_current_user),
):
    task = generate_thumbnail_task.delay(object_key=object_key, sizes=sizes)
    return TaskOut(task_id=task.id)


@router.post("/price-suggestions/precompute", response_model=TaskOut, status_code=status.HTTP_202_ACCEPTED)
async def price_precompute(current=Depends(get_current_user)):
    task = precompute_recent_prices.delay()
    return TaskOut(task_id=task.id)


@router.post("/cleanup/orphans", response_model=TaskOut, status_code=status.HTTP_202_ACCEPTED)
async def cleanup_orphans(prefix: str = "listings/", current=Depends(get_current_user)):
    task = cleanup_orphan_objects.delay(prefix=prefix)
    return TaskOut(task_id=task.id)


@router.get("/tasks/{task_id}", response_model=TaskStatusOut)
async def task_status(task_id: str, current=Depends(get_current_user)):
    res = AsyncResult(id=task_id, app=celery_app)
    payload = res.result if isinstance(res.result, dict) else None
    return TaskStatusOut(task_id=task_id, state=res.state, result=payload)
