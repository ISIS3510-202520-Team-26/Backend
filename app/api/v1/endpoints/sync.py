from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.sync_service import get_catalog_delta, not_modified

router = APIRouter(prefix="/sync", tags=["sync"])

@router.get("/delta", status_code=status.HTTP_200_OK)
async def sync_delta(
    response: Response,
    since: str | None = None,
    if_none_match: str | None = Header(default=None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
):
    since_dt: datetime | None = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except Exception:
            since_dt = None

    payload, etag, last_modified = await get_catalog_delta(db, since=since_dt, limit=200)

    if not_modified(if_none_match, etag):
        response.status_code = status.HTTP_304_NOT_MODIFIED
        return

    response.headers["ETag"] = etag
    response.headers["Last-Modified"] = last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return payload
