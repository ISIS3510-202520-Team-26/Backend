from __future__ import annotations
import time
from typing import Callable, Awaitable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from redis.asyncio import Redis
from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self._redis: Redis | None = None

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._redis is None:
            self._redis = Redis.from_url(settings.redis_url, decode_responses=True)

        auth = request.headers.get("Authorization", "")
        ident = auth[-20:] if auth.startswith("Bearer ") else request.client.host 
        route = request.scope.get("path", "/")
        now = int(time.time())
        bucket = now // self.window
        key = f"ratelimit:{route}:{ident}:{bucket}"

        pipe = self._redis.pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, self.window + 1)
        count, _ = await pipe.execute()

        remaining = max(self.max_requests - int(count), 0)
        if remaining <= 0:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        resp = await call_next(request)
        resp.headers["X-RateLimit-Limit"] = str(self.max_requests)
        resp.headers["X-RateLimit-Remaining"] = str(remaining)
        return resp
