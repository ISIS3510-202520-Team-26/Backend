from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
import os, json
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.listing import Listing

# ---------- Priors en memoria / archivo (sin DB) ----------
_DEFAULT_PRIORS = {
    "category": {
        "books":   {"p25": 1500,   "p50": 3000,    "p75": 5000},
        "phones":  {"p25": 200000, "p50": 400000,  "p75": 700000},
        "laptops": {"p25": 800000, "p50": 1200000, "p75": 1800000},
        "bikes":   {"p25": 300000, "p50": 600000,  "p75": 900000},
    },
    "brand": {}
}

def _load_priors_from_file(path: str = "priors.json") -> Dict[str, Any]:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _DEFAULT_PRIORS

_PRIORS = _load_priors_from_file()

_CONDITION_MULT = {
    "new": 1.00, "like_new": 0.90, "good": 0.80, "fair": 0.65, "poor": 0.50
}

def _round_to(x: int, quantum: int = 100) -> int:
    return int(round(x / quantum) * quantum)

def _pick_prior(category_id: str, brand_id: Optional[str]) -> Optional[Dict[str, int]]:
    cat = (category_id or "").lower()
    br = (brand_id or "").lower() if brand_id else None
    if br and cat in _PRIORS.get("brand", {}) and br in _PRIORS["brand"][cat]:
        return {k: int(v) for k, v in _PRIORS["brand"][cat][br].items()}
    if cat in _PRIORS.get("category", {}):
        return {k: int(v) for k, v in _PRIORS["category"][cat].items()}
    return None

def _depreciation_factor(months: Optional[int], kind: str = "electronics") -> float:
    if months is None:
        return 0.70
    m = max(0, months)
    if kind in ("phones", "laptops", "electronics"):
        # suave exponencial por año
        return 0.90 * (0.85 ** (m / 12.0))
    return max(0.40, 1.0 - 0.02 * m)

def _apply_bounds(p50: int) -> Tuple[int, int, int]:
    return int(round(p50 * 0.75)), int(p50), int(round(p50 * 1.40))

def _mix(pr: Dict[str, int], smp: Dict[str, int], n: int,
         *, w_prior_base: int = 20, n_cap: int = 40) -> Dict[str, int]:
    w_data = min(max(n, 0), n_cap)
    w_prior = w_prior_base
    out = {}
    for k in ("p25", "p50", "p75"):
        out[k] = int(round((w_prior * pr[k] + w_data * smp[k]) / (w_prior + w_data)))
    return out

async def _get_sample_quantiles(
    db: AsyncSession,
    where: list
) -> Tuple[Optional[int], Optional[int], Optional[int], int]:
    count_stmt = sa.select(sa.func.count()).where(sa.and_(*where))
    n = (await db.execute(count_stmt)).scalar_one()
    if n == 0:
        return None, None, None, 0

    stmt = sa.select(
        sa.func.percentile_cont(0.25).within_group(Listing.price_cents.asc()),
        sa.func.percentile_cont(0.50).within_group(Listing.price_cents.asc()),
        sa.func.percentile_cont(0.75).within_group(Listing.price_cents.asc()),
    ).where(sa.and_(*where))
    p25, p50, p75 = (await db.execute(stmt)).one()
    if p50 is None:
        return None, None, None, n
    return int(p25), int(p50), int(p75), n

async def suggest_price_cents(
    db: AsyncSession,
    *,
    category_id: str,
    brand_id: Optional[str] = None,
    condition: Optional[str] = None,
    msrp_cents: Optional[int] = None,
    months_since_release: Optional[int] = None,
    rounding_quantum: int = 100,
) -> Optional[dict]:
    """
    Retorna:
    {
      "suggested": int, "p25": int, "p50": int, "p75": int,
      "n": int, "source": "local_median|prior_only|prior+local_mix|msrp_heuristic|hardcoded_fallback"
    }
    """
    if not category_id:
        return None

    cutoff = sa.func.now() - sa.text("INTERVAL '90 days'")
    where = [Listing.is_active.is_(True), Listing.category_id == category_id, Listing.created_at >= cutoff]
    if brand_id:
        where.append(Listing.brand_id == brand_id)

    # 1) Muestra local
    try:
        p25_loc, p50_loc, p75_loc, n = await _get_sample_quantiles(db, where)
    except Exception:
        # por si el dialecto no soporta ordered-set
        p25_loc, p50_loc, p75_loc, n = None, None, None, 0

    # 2) MSRP heurístico (si no hay muestra suficiente)
    if (n == 0 or p50_loc is None) and msrp_cents and msrp_cents > 0:
        kind = "electronics" if category_id in ("phones", "laptops", "electronics") else category_id
        dep = _depreciation_factor(months_since_release, kind=kind)
        cond_mult = _CONDITION_MULT.get((condition or "good"), 0.80)
        est = int(round(msrp_cents * dep * cond_mult))
        p25, p50, p75 = _apply_bounds(est)
        return {
            "suggested": _round_to(p50, rounding_quantum),
            "p25": _round_to(p25, rounding_quantum),
            "p50": _round_to(p50, rounding_quantum),
            "p75": _round_to(p75, rounding_quantum),
            "n": n,
            "source": "msrp_heuristic",
        }

    # 3) Priors en memoria
    prior = _pick_prior(category_id, brand_id)

    # 4) Decidir mezcla / fuente
    if p50_loc is not None and n > 0:
        local = {"p25": p25_loc, "p50": p50_loc, "p75": p75_loc}
        if prior:
            mixed = _mix(prior, local, n, w_prior_base=20, n_cap=40)
            p25, p50, p75 = mixed["p25"], mixed["p50"], mixed["p75"]
            source = "prior+local_mix"
        else:
            p25, p50, p75 = local["p25"], local["p50"], local["p75"]
            source = "local_median"
    elif prior:
        p25, p50, p75 = prior["p25"], prior["p50"], prior["p75"]
        source = "prior_only"
    else:
        # último recurso
        mid = 100000
        p25, p50, p75 = int(mid * 0.75), mid, int(mid * 1.40)
        source = "hardcoded_fallback"

    return {
        "suggested": _round_to(p50, rounding_quantum),
        "p25": _round_to(p25, rounding_quantum),
        "p50": _round_to(p50, rounding_quantum),
        "p75": _round_to(p75, rounding_quantum),
        "n": n,
        "source": source,
    }
