"""Sector routes — list available industry sectors."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.database import get_db, AsyncSession
from app.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.sector import Sector, SectorEnum, SECTOR_PRESETS

router = APIRouter()


class SectorOut(BaseModel):
    id: int
    type: str
    name: str
    icon: str
    description: str | None
    color: str
    visits_multiplier: float
    conversion_multiplier: float
    avg_cpc: float
    revenue_multiplier: float
    is_active: bool

    model_config = {"from_attributes": True}


class SectorListOut(BaseModel):
    total: int
    items: list[SectorOut]


@router.get("", response_model=SectorListOut)
async def list_sectors(db: AsyncSession = Depends(get_db)):
    """Return all active sectors. If DB is empty, return presets."""
    result = await db.execute(select(Sector).where(Sector.is_active == True))
    sectors = result.scalars().all()

    if not sectors:
        # Return in-memory presets
        items = []
        for i, (key, preset) in enumerate(SECTOR_PRESETS.items(), 1):
            items.append(SectorOut(
                id=i, type=key, name=preset["name"], icon=preset["icon"],
                description=preset["description"], color=preset.get("color", "gray"),
                visits_multiplier=preset["visits_multiplier"],
                conversion_multiplier=preset["conversion_multiplier"],
                avg_cpc=preset["avg_cpc"],
                revenue_multiplier=preset["revenue_multiplier"],
                is_active=True,
            ))
        return SectorListOut(total=len(items), items=items)

    return SectorListOut(
        total=len(sectors),
        items=[SectorOut(
            id=s.id, type=s.type.value if hasattr(s.type, 'value') else s.type,
            name=s.name, icon=s.icon, description=s.description,
            color=s.color, visits_multiplier=s.visits_multiplier,
            conversion_multiplier=s.conversion_multiplier,
            avg_cpc=s.avg_cpc, revenue_multiplier=s.revenue_multiplier,
            is_active=s.is_active,
        ) for s in sectors]
    )


@router.post("/seed", response_model=list[SectorOut], status_code=201)
async def seed_sectors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seed the 8 preset sectors. Admin only, idempotent."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")

    created = []
    for key, preset in SECTOR_PRESETS.items():
        exist = await db.execute(
            select(Sector).where(Sector.type == SectorEnum(key))
        )
        if exist.scalar_one_or_none():
            continue

        sector = Sector(
            type=SectorEnum(key),
            name=preset["name"],
            icon=preset["icon"],
            description=preset["description"],
            color=preset.get("color", "gray"),
            visits_multiplier=preset["visits_multiplier"],
            conversion_multiplier=preset["conversion_multiplier"],
            avg_cpc=preset["avg_cpc"],
            revenue_multiplier=preset["revenue_multiplier"],
        )
        db.add(sector)
        created.append(sector)

    await db.commit()
    for s in created:
        await db.refresh(s)

    return [SectorOut(
        id=s.id, type=s.type.value, name=s.name, icon=s.icon,
        description=s.description, color=s.color,
        visits_multiplier=s.visits_multiplier,
        conversion_multiplier=s.conversion_multiplier,
        avg_cpc=s.avg_cpc, revenue_multiplier=s.revenue_multiplier,
        is_active=s.is_active,
    ) for s in created]
