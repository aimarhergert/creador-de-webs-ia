import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.asset import Asset, AssetStatus
from app.services.analytics_engine import get_asset_summary

logger = logging.getLogger(__name__)

ROI_SCALE_THRESHOLD = 3.0
ROI_KILL_THRESHOLD = 1.0
MIN_DAYS_BEFORE_DECISION = 7


async def evaluate_asset(db: AsyncSession, asset_id: int) -> dict:
    """
    ROI-based decision engine:
      ROI > 3  → SCALE
      ROI < 1  → KILL
      else     → OPTIMIZE
    """
    summary = await get_asset_summary(db, asset_id)
    roi = summary["roi"]
    days = summary["days_tracked"]

    if days < MIN_DAYS_BEFORE_DECISION:
        decision = "wait"
        reason = f"Solo {days} día(s) de datos. Mínimo {MIN_DAYS_BEFORE_DECISION} para decidir."
    elif roi >= ROI_SCALE_THRESHOLD:
        decision = "scale"
        reason = f"ROI {roi:.2f} > {ROI_SCALE_THRESHOLD} → ESCALAR"
    elif roi < ROI_KILL_THRESHOLD:
        decision = "kill"
        reason = f"ROI {roi:.2f} < {ROI_KILL_THRESHOLD} → ELIMINAR"
    else:
        decision = "optimize"
        reason = f"ROI {roi:.2f} entre umbrales → OPTIMIZAR"

    logger.info(f"[Optimization] Asset {asset_id}: {decision.upper()} — {reason}")

    # Apply decision to asset
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if asset:
        if decision == "scale":
            asset.status = AssetStatus.SCALING
        elif decision == "kill":
            asset.status = AssetStatus.KILLED
        elif decision == "optimize":
            asset.status = AssetStatus.OPTIMIZING
        await db.flush()

    return {
        "asset_id": asset_id,
        "decision": decision,
        "reason": reason,
        "roi": roi,
        "days_tracked": days,
        "summary": summary,
    }


async def run_portfolio_optimization(db: AsyncSession) -> list[dict]:
    """Evaluate all LIVE assets in the portfolio."""
    result = await db.execute(
        select(Asset).where(Asset.status.in_([
            AssetStatus.LIVE, AssetStatus.OPTIMIZING, AssetStatus.SCALING
        ]))
    )
    assets = result.scalars().all()
    logger.info(f"[Optimization] Evaluando {len(assets)} activo(s)")

    results = []
    for asset in assets:
        evaluation = await evaluate_asset(db, asset.id)
        results.append(evaluation)

    await db.commit()
    return results
