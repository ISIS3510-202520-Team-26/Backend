from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field

# Opcional: enumerar las condiciones admitidas en tu UI
Condition = Literal["new", "like_new", "good", "fair", "poor"]

# El algoritmo que guardamos en DB (column algorithm VARCHAR(40))
Algorithm = Literal[
    "local_median",
    "prior_only",
    "prior+local_mix",
    "msrp_heuristic",
    "hardcoded_fallback",
]

class PriceSuggestionOut(BaseModel):
    # Campos que tu modelo/queries recientes pueden devolver
    id: Optional[str] = None
    listing_id: Optional[str] = None
    suggested_price_cents: int
    algorithm: str = Field(..., description="Estrategia usada (se guarda en DB)")
    created_at: Optional[str] = None

    # Metadatos extra SOLO para respuesta del GET/POST compute (no se guardan)
    p25: Optional[int] = None
    p50: Optional[int] = None
    p75: Optional[int] = None
    n: Optional[int] = None
    source: Optional[str] = None  # suele coincidir con algorithm

class SuggestQuery(BaseModel):
    category_id: str
    brand_id: Optional[str] = None
    condition: Optional[Condition] = None
    msrp_cents: Optional[int] = None
    months_since_release: Optional[int] = None
    rounding_quantum: Optional[int] = 100

class ComputeIn(BaseModel):
    category_id: str
    brand_id: Optional[str] = None
    condition: Optional[Condition] = None
    msrp_cents: Optional[int] = None
    months_since_release: Optional[int] = None
    rounding_quantum: Optional[int] = 100
