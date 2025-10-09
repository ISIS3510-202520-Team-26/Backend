from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel, IdOut

class ListingPhotoOut(IdOut):
    listing_id: str
    storage_key: str
    image_url: str | None = None
    width: int | None = None
    height: int | None = None
    created_at: datetime

class PresignIn(BaseModel):
    listing_id: str
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., pattern=r"^[\w\-\.\+]+\/[\w\-\.\+]+$") 

class PresignOut(BaseModel):
    upload_url: str
    object_key: str

class ConfirmIn(BaseModel):
    listing_id: str
    object_key: str

class ConfirmOut(BaseModel):
    preview_url: str
