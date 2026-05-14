from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import require_api_key
from app.services.analytics_engine import record_metrics, get_asset_summary, get_portfolio_summary

router = APIRouter()


class MetricsPayload(BaseModel):
    visits: int = 0
    conversions: int = 0
    revenue: float = 0.0
    cost: float = 0.0


# ── PUBLIC — tracking pixel calls this from deployed pages ───────────────────
@router.post("/{asset_id}/track")
async def track_metrics(
    asset_id: int,
    payload: MetricsPayload,
    db: AsyncSession = Depends(get_db),
):
    """Receive metrics from tracking pixels embedded in deployed pages."""
    metrics = await record_metrics(
        db,
        asset_id,
        visits=payload.visits,
        conversions=payload.conversions,
        revenue=payload.revenue,
        cost=payload.cost,
    )
    return {
        "status": "recorded",
        "asset_id": asset_id,
        "roi": metrics.roi,
        "conversion_rate": metrics.conversion_rate,
    }


# ── PROTECTED — dashboard & API access ───────────────────────────────────────
@router.get("/portfolio/summary", dependencies=[Depends(require_api_key)])
async def portfolio_summary(db: AsyncSession = Depends(get_db)):
    return await get_portfolio_summary(db)


@router.get("/{asset_id}/summary", dependencies=[Depends(require_api_key)])
async def asset_summary(asset_id: int, db: AsyncSession = Depends(get_db)):
    return await get_asset_summary(db, asset_id)
