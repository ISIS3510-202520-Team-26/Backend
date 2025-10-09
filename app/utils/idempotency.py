from __future__ import annotations
from typing import Optional
import asyncio
from redis.asyncio import Redis

KEY_FMT = "idem:{scope}:{key}"

async def check_and_set(
    redis: Redis,
    *,
    scope: str,
    key: str,
    ttl_seconds: int = 3600,
) -> bool:
    """
    Devuelve True si la key se estableció (primera vez).
    Devuelve False si ya existía (reintento duplicado).
    Usa SET NX EX para ser atómico.
    """
    r = await redis.set(KEY_FMT.format(scope=scope, key=key), "1", nx=True, ex=ttl_seconds)
    return bool(r)

async def clear(redis: Redis, *, scope: str, key: str) -> None:
    await redis.delete(KEY_FMT.format(scope=scope, key=key))
