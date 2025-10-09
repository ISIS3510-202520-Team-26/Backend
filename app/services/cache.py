from __future__ import annotations
from typing import Any, Optional
import asyncio
import orjson
from redis.asyncio import Redis
from app.core.config import settings

_redis: Optional[Redis] = None
_lock = asyncio.Lock()

async def _get_client() -> Redis:
    global _redis
    if _redis is None:
        async with _lock:
            if _redis is None:
                _redis = Redis.from_url(settings.redis_url, decode_responses=False)
    return _redis

def _dumps(obj: Any) -> bytes:
    return orjson.dumps(obj)

def _loads(data: bytes) -> Any:
    return orjson.loads(data)

async def get_json(key: str) -> Any | None:
    r = await _get_client()
    val = await r.get(key)
    return None if val is None else _loads(val)

async def set_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    r = await _get_client()
    data = _dumps(value)
    if ttl_seconds:
        await r.setex(key, ttl_seconds, data)
    else:
        await r.set(key, data)

async def delete(key: str) -> None:
    r = await _get_client()
    await r.delete(key)

async def close() -> None:
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
