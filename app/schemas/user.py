from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, constr
from app.schemas.common import ORMModel, IdOut
from datetime import datetime

Sha256Str = constr(strip_whitespace=True, min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$")

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    campus: str | None = Field(None, max_length=120)

class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    campus: str | None = Field(None, max_length=120)

class UserOut(IdOut):
    name: str
    email: str
    campus: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None

class ContactsMatchIn(BaseModel):
    email_hashes: list[Sha256Str] = Field(default_factory=list)

class ContactMatchOut(BaseModel):
    user_id: str
    name: str
    email: str  

