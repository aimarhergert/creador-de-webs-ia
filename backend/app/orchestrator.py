import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, AssetStatus
from app.models.deployment import Deployment, DeploymentPlatform, DeploymentStatus
from app.services import (
    market_engine,
    asset_factory,
    deployment_engine,
    monetization_engine,
)
from app.schemas.orchestrator import PipelineRequest

logger = logging.getLogger(__name__)


async def run_pipeline(request: PipelineRequest, db: AsyncSession) -> Asset:
    """
    Full autonomous pipeline:
      1. scan_market()
      2. create_asset()
      3. deploy_asset()
      4. attach_monetization()
      → Asset persisted at each step with status updates
    """
    # ── Step 1: Market Analysis ──────────────────────────────────────────
    logger.info(f"\n{'='*60}\n[Pipeline] INICIO: {request.keyword}\n{'='*60}")
    opportunity = await market_engine.scan_market(request.keyword)

    # Create asset record
    asset = Asset(
        keyword=request.keyword,
        type=request.type,
        monetization_model=request.monetization_model,
        status=AssetStatus.GENERATING,
        market_score=opportunity.score,
        cpc_estimate=opportunity.cpc,
        cost=0.05,  # Coste estimado por llamada a la IA
    )
    db.add(asset)
    await db.flush()  # Get ID without committing
    logger.info(f"[Pipeline] Asset creado con ID: {asset.id}")

    # ── Step 2: Generate Content ──────────────────────────────────────────
    try:
        files = await asset_factory.generate_asset(
            request.keyword, request.type, request.monetization_model
        )
        html_content = files.get("index.html", "")

        # ── Step 3: Monetization Injection ────────────────────────────────
        html_content = await monetization_engine.attach_monetization(
            html_content, request.keyword, request.monetization_model, request.type,
            asset_id=asset.id,
        )
        files["index.html"] = html_content
        asset.content_html = html_content

        # ── Step 4: Deployment ────────────────────────────────────────────
        asset.status = AssetStatus.DEPLOYING
        await db.flush()

        deploy_result = await deployment_engine.deploy_asset(request.keyword, files)

        asset.url = deploy_result["url"]
        asset.repo_name = deploy_result.get("repo_name", "")
        asset.status = AssetStatus.LIVE
        asset.updated_at = datetime.utcnow()

        deployment = Deployment(
            asset_id=asset.id,
            platform=DeploymentPlatform(deploy_result["platform"]),
            url=deploy_result["url"],
            status=DeploymentStatus.SUCCESS,
            deploy_id=deploy_result.get("deploy_id", ""),
        )
        db.add(deployment)

    except Exception as exc:
        logger.error(f"[Pipeline] ERROR en asset {asset.id}: {exc}")
        asset.status = AssetStatus.ERROR
        asset.error_message = str(exc)
        asset.updated_at = datetime.utcnow()
        await db.commit()
        raise

    await db.commit()
    await db.refresh(asset)

    logger.info(
        f"[Pipeline] COMPLETADO — Asset {asset.id} LIVE en: {asset.url}\n{'='*60}\n"
    )
    return asset
