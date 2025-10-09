from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from typing import Any, Tuple

def make_etag(payload: Any) -> str:
    if isinstance(payload, (bytes, bytearray)):
        b = bytes(payload)
    elif isinstance(payload, str):
        b = payload.encode("utf-8")
    else:
        import orjson
        b = orjson.dumps(payload)
    return hashlib.sha1(b).hexdigest()

def last_modified_now() -> str:
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

def etag_headers(payload: Any) -> dict:
    return {"ETag": make_etag(payload), "Last-Modified": last_modified_now()}
