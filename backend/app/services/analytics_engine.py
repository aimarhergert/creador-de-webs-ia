import logging
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.metrics import Metrics
from app.models.asset import Asset

logger = logging.getLogger(__name__)


async def record_metrics(
    db: AsyncSession,
    asset_id: int,
    visits: int = 0,
    conversions: int = 0,
    revenue: float = 0.0,
    cost: float = 0.0,
) -> Metrics:
    """Upsert daily metrics for an asset."""
    today = date.today()

    result = await db.execute(
        select(Metrics).where(Metrics.asset_id == asset_id, Metrics.date == today)
    )
    metrics = result.scalar_one_or_none()

    if metrics:
        metrics.visits += visits
        metrics.conversions += conversions
        metrics.revenue += revenue
        metrics.cost += cost
    else:
        metrics = Metrics(
            asset_id=asset_id,
            date=today,
            visits=visits,
            conversions=conversions,
            revenue=revenue,
            cost=cost,
        )
        db.add(metrics)

    # Sync totals to Asset row
    asset_result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = asset_result.scalar_one_or_none()
    if asset:
        totals = await db.execute(
            select(
                func.sum(Metrics.revenue),
                func.sum(Metrics.cost),
            ).where(Metrics.asset_id == asset_id)
        )
        total_revenue, total_cost = totals.one()
        asset.revenue = float(total_revenue or 0)
        asset.cost = float(total_cost or 0)
        asset.updated_at = datetime.utcnow()

    await db.flush()
    logger.info(f"[Analytics] Asset {asset_id} — visits: {visits}, revenue: {revenue:.2f}€")
    return metrics


async def get_asset_summary(db: AsyncSession, asset_id: int) -> dict:
    result = await db.execute(
        select(
            func.sum(Metrics.visits).label("total_visits"),
            func.sum(Metrics.conversions).label("total_conversions"),
            func.sum(Metrics.revenue).label("total_revenue"),
            func.sum(Metrics.cost).label("total_cost"),
            func.count(Metrics.id).label("days_tracked"),
        ).where(Metrics.asset_id == asset_id)
    )
    row = result.one()
    total_revenue = float(row.total_revenue or 0)
    total_cost = float(row.total_cost or 0)

    return {
        "asset_id": asset_id,
        "total_visits": int(row.total_visits or 0),
        "total_conversions": int(row.total_conversions or 0),
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "roi": round(total_revenue / total_cost, 2) if total_cost > 0 else 0.0,
        "days_tracked": int(row.days_tracked or 0),
    }


async def get_portfolio_summary(db: AsyncSession) -> dict:
    result = await db.execute(
        select(
            func.count(Asset.id).label("total_assets"),
            func.sum(Asset.revenue).label("total_revenue"),
            func.sum(Asset.cost).label("total_cost"),
        )
    )
    row = result.one()
    total_revenue = float(row.total_revenue or 0)
    total_cost = float(row.total_cost or 0)

    return {
        "total_assets": int(row.total_assets or 0),
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "portfolio_roi": round(total_revenue / total_cost, 2) if total_cost > 0 else 0.0,
    }
