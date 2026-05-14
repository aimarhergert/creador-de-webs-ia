from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.user import User
from app.models.asset import Asset, AssetStatus
from app.models.activity import ActivityEvent
from app.models.audit_log import AuditLog
from app.schemas.admin import UserAdminOut, UserAdminUpdate, SystemStats, AuditLogOut

router = APIRouter()


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    from datetime import date
    from app.models.metrics import Metrics

    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )).scalar()

    total_assets = (await db.execute(select(func.count(Asset.id)))).scalar()
    live_assets = (await db.execute(
        select(func.count(Asset.id)).where(Asset.status == AssetStatus.LIVE)
    )).scalar()
    scaling_assets = (await db.execute(
        select(func.count(Asset.id)).where(Asset.status == AssetStatus.SCALING)
    )).scalar()
    killed_assets = (await db.execute(
        select(func.count(Asset.id)).where(Asset.status == AssetStatus.KILLED)
    )).scalar()

    total_revenue = (await db.execute(select(func.sum(Asset.revenue)))).scalar() or 0.0

    total_events = (await db.execute(select(func.count(ActivityEvent.id)))).scalar()

    today = date.today()
    sim_ticks = (await db.execute(
        select(func.count(Metrics.id)).where(Metrics.date == today)
    )).scalar()

    return SystemStats(
        total_users=total_users,
        active_users=active_users,
        total_assets=total_assets,
        live_assets=live_assets,
        scaling_assets=scaling_assets,
        killed_assets=killed_assets,
        total_revenue=round(float(total_revenue), 2),
        total_events=total_events,
        sim_ticks_today=sim_ticks,
    )


@router.get("/users", response_model=list[UserAdminOut])
async def list_users(
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/users/{user_id}", response_model=UserAdminOut)
async def update_user(
    user_id: int,
    body: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="No puedes modificar tu propia cuenta de admin")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/simulation/tick")
async def trigger_simulation_tick(
    _: User = Depends(get_current_admin),
):
    """Manually fire one simulation tick."""
    from app.workers.simulation import simulate_traffic_tick
    simulate_traffic_tick.delay()
    return {"message": "Simulation tick enqueued"}


@router.post("/simulation/optimize")
async def trigger_optimization(
    _: User = Depends(get_current_admin),
):
    """Manually trigger portfolio optimization cycle."""
    from app.workers.tasks import optimize_portfolio_task
    optimize_portfolio_task.delay()
    return {"message": "Optimization cycle enqueued"}


@router.get("/logs", response_model=list[AuditLogOut])
async def get_audit_logs(
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(AuditLog)
        .offset(offset)
        .limit(limit)
        .order_by(AuditLog.created_at.desc())
    )
    return result.scalars().all()
