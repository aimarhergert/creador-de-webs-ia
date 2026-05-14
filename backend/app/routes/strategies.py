from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.dependencies import get_current_user
from app.models.strategy import Strategy, StrategyType, STRATEGY_PRESETS
from app.models.user import User
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyOut, StrategyListOut

router = APIRouter()


@router.get("", response_model=StrategyListOut)
async def list_strategies(
    include_presets: bool = Query(default=True),
    type: StrategyType | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Strategy).where(
        or_(Strategy.is_preset == True, Strategy.user_id == current_user.id)
    )
    if not include_presets:
        query = query.where(Strategy.is_preset == False, Strategy.user_id == current_user.id)
    if type:
        query = query.where(Strategy.type == type)

    count = await db.execute(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.order_by(Strategy.is_preset.desc(), Strategy.name))
    return StrategyListOut(total=count.scalar(), items=result.scalars().all())


@router.get("/{strategy_id}", response_model=StrategyOut)
async def get_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")
    if not strategy.is_preset and strategy.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta estrategia")
    return strategy


@router.post("", response_model=StrategyOut, status_code=201)
async def create_strategy(
    body: StrategyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = Strategy(**body.model_dump(), user_id=current_user.id, is_preset=False)
    db.add(strategy)
    await db.commit()
    await db.refresh(strategy)
    return strategy


@router.patch("/{strategy_id}", response_model=StrategyOut)
async def update_strategy(
    strategy_id: int,
    body: StrategyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")
    if strategy.is_preset:
        raise HTTPException(status_code=400, detail="Los presets del sistema no se pueden modificar")
    if strategy.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(strategy, field, value)

    await db.commit()
    await db.refresh(strategy)
    return strategy


@router.delete("/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")
    if strategy.is_preset:
        raise HTTPException(status_code=400, detail="No se pueden eliminar los presets del sistema")
    if strategy.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")

    await db.delete(strategy)
    await db.commit()


@router.post("/seed-presets", response_model=list[StrategyOut], status_code=201)
async def seed_preset_strategies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seed the 6 system preset strategies. Safe to call multiple times (idempotent)."""
    from app.models.user import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")

    created = []
    for strat_type, params in STRATEGY_PRESETS.items():
        existing = await db.execute(
            select(Strategy).where(Strategy.type == strat_type, Strategy.is_preset == True)
        )
        if existing.scalar_one_or_none():
            continue

        name_map = {
            "seo_growth": "SEO Growth",
            "affiliate_arbitrage": "Affiliate Arbitrage",
            "lead_generation": "Lead Generation",
            "micro_saas": "Micro SaaS",
            "aggressive_scaling": "Aggressive Scaling",
            "conservative_roi": "Conservative ROI",
        }
        strategy = Strategy(
            name=name_map[strat_type],
            type=StrategyType(strat_type),
            is_preset=True,
            **params,
        )
        db.add(strategy)
        created.append(strategy)

    await db.commit()
    for s in created:
        await db.refresh(s)
    return created
