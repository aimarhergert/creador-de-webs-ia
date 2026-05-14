import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.asset import Asset, AssetStatus, AssetType
from app.schemas.asset import (
    AssetUpdate,
    AssetOut,
    AssetListOut,
    AssetWithFilesOut,
    GenerateRequest,
)
from app.services.asset_factory import generate_landing_page

logger = logging.getLogger(__name__)
router = APIRouter()


# ── POST /api/assets/generate ────────────────────────────────────────────────
@router.post(
    "/generate",
    response_model=AssetWithFilesOut,
    status_code=201,
    summary="Generate a website with Claude AI",
    description=(
        "Calls Claude to generate a complete website (HTML+CSS+JS) for the given keyword, "
        "persists it to the database, and returns the asset with the generated file contents."
    ),
)
async def generate_asset_endpoint(
    body: GenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> AssetWithFilesOut:
    logger.info(f"[Route] POST /generate — keyword='{body.keyword}' type={body.type.value}")

    try:
        asset = await generate_landing_page(
            keyword=body.keyword,
            db=db,
            asset_type=body.type,
            monetization=body.monetization_model,
        )
    except Exception as exc:
        # Asset record was already saved with status=ERROR by the service layer
        raise HTTPException(
            status_code=502,
            detail=f"Error generando el activo: {exc}",
        ) from exc

    return AssetWithFilesOut(
        **AssetOut.model_validate(asset).model_dump(),
        files=asset.files,
    )


# ── GET /api/assets/{asset_id}/files ─────────────────────────────────────────
@router.get(
    "/{asset_id}/files",
    response_model=dict[str, str],
    summary="Get generated file contents for an asset",
    description="Returns the raw HTML, CSS and JS files generated for this asset.",
)
async def get_asset_files(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset no encontrado")
    if not asset.content_files:
        raise HTTPException(
            status_code=404,
            detail="Este asset aún no tiene archivos generados. Estado actual: " + asset.status.value,
        )
    return asset.files


# ── GET /api/assets ───────────────────────────────────────────────────────────
@router.get("", response_model=AssetListOut)
async def list_assets(
    status: Optional[AssetStatus] = None,
    type: Optional[AssetType] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Asset)
    if status:
        query = query.where(Asset.status == status)
    if type:
        query = query.where(Asset.type == type)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    result = await db.execute(
        query.offset(offset).limit(limit).order_by(Asset.created_at.desc())
    )
    items = result.scalars().all()
    return AssetListOut(total=total, items=items)


# ── GET /api/assets/{asset_id} ────────────────────────────────────────────────
@router.get("/{asset_id}", response_model=AssetOut)
async def get_asset(asset_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset no encontrado")
    return asset


# ── PATCH /api/assets/{asset_id} ──────────────────────────────────────────────
@router.patch("/{asset_id}", response_model=AssetOut)
async def update_asset(asset_id: int, data: AssetUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset no encontrado")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)
    return asset


# ── DELETE /api/assets/{asset_id} ─────────────────────────────────────────────
@router.delete("/{asset_id}", status_code=204)
async def delete_asset(asset_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset no encontrado")
    await db.delete(asset)
    await db.commit()
