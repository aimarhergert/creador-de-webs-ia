"""
AROS Autonomous Agent — Market Research + Asset Creation Loop.

The agent:
  1. Researches the market to find winning topics
  2. Selects the best opportunities based on score
  3. Auto-creates assets (landing pages) for top picks
  4. Generates blog posts to support them
  5. Returns a complete report of what was done

Can run manually or on schedule via Celery beat.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.asset import Asset, AssetType, AssetStatus, MonetizationModel
from app.models.activity import ActivityEvent, EventType
from app.models.blog import BlogPost, BlogStatus
from app.services.market_research import research_market, KeywordOpportunity, MarketReport
from app.services.ai_provider import generate_with_fallback

logger = logging.getLogger(__name__)


@dataclass
class AgentRunResult:
    started_at: datetime = field(default_factory=datetime.utcnow)
    keywords_found: int = 0
    opportunities_analyzed: int = 0
    assets_created: int = 0
    blog_posts_created: int = 0
    errors: list[str] = field(default_factory=list)
    created_asset_ids: list[int] = field(default_factory=list)
    top_keyword: str = ""
    market_report: Optional[MarketReport] = None


async def run_autonomous_agent(
    sectors: list[str] | None = None,
    max_assets: int = 3,
    dry_run: bool = False,
) -> AgentRunResult:
    """
    Full autonomous agent run:
    Research → Score → Select → Create → Report
    """
    result = AgentRunResult()
    logger.info("🤖 [AutonomousAgent] Starting autonomous run...")

    # ── Step 1: Market Research ─────────────────────────────────────────
    logger.info("[AutonomousAgent] 📊 Step 1: Market Research")
    try:
        report = await research_market(sectors=sectors, deep=True)
        result.market_report = report
        result.keywords_found = report.total_keywords_found
        result.opportunities_analyzed = len(report.top_opportunities)

        if report.top_opportunities:
            result.top_keyword = report.top_opportunities[0].keyword

        logger.info(
            f"[AutonomousAgent] Found {result.keywords_found} keywords, "
            f"top {result.opportunities_analyzed} opportunities"
        )
    except Exception as e:
        result.errors.append(f"Market research failed: {e}")
        logger.error(f"Market research failed: {e}")
        return result

    # ── Step 2: Select winners ───────────────────────────────────────────
    winners = [o for o in (report.top_opportunities or []) if o.opportunity_score >= 55][:max_assets]
    logger.info(f"[AutonomousAgent] 🎯 Step 2: Selected {len(winners)} winners (score >= 55)")

    if not winners:
        result.errors.append("No opportunities with score >= 55 found")
        return result

    # ── Step 3: Create assets ────────────────────────────────────────────
    if dry_run:
        logger.info("[AutonomousAgent] 🧪 Dry run — skipping asset creation")
        result.assets_created = len(winners)
        result.blog_posts_created = len(winners)
        return result

    logger.info(f"[AutonomousAgent] 🏗️  Step 3: Creating {len(winners)} assets")

    for winner in winners:
        try:
            asset = await _create_asset_for_keyword(
                keyword=winner.keyword,
                sector=winner.sector,
                asset_type=winner.suggested_asset_type,
                monetization=winner.suggested_monetization,
            )
            if asset:
                result.assets_created += 1
                result.created_asset_ids.append(asset.id)
                logger.info(f"[AutonomousAgent] ✅ Asset #{asset.id}: {winner.keyword}")

                # Also create a blog post for each asset
                try:
                    blog = await _create_blog_for_asset(asset.keyword, winner.sector, asset.id)
                    if blog:
                        result.blog_posts_created += 1
                except Exception as e:
                    logger.warning(f"Blog creation failed for asset #{asset.id}: {e}")

        except Exception as e:
            msg = f"Asset creation failed for '{winner.keyword}': {e}"
            result.errors.append(msg)
            logger.error(msg)

    # ── Step 4: Activity event ───────────────────────────────────────────
    try:
        async with AsyncSessionLocal() as db:
            event = ActivityEvent(
                event_type=EventType.PIPELINE_DONE,
                title=f"🤖 Agente autónomo: {result.assets_created} activos creados",
                description=(
                    f"Investigación de mercado completada. "
                    f"{result.keywords_found} keywords analizadas. "
                    f"Top pick: '{result.top_keyword}'. "
                    f"{result.assets_created} assets y {result.blog_posts_created} blogs generados."
                ),
                data={
                    "assets_created": result.assets_created,
                    "blogs_created": result.blog_posts_created,
                    "top_keyword": result.top_keyword,
                },
            )
            db.add(event)
            await db.commit()
    except Exception:
        pass

    logger.info(
        f"[AutonomousAgent] 🏁 Run complete — "
        f"{result.assets_created} assets, {result.blog_posts_created} blogs, "
        f"{len(result.errors)} errors"
    )
    return result


async def _create_asset_for_keyword(
    keyword: str,
    sector: str,
    asset_type: str = "landing_page",
    monetization: str = "affiliates",
) -> Optional[Asset]:
    """Create a single asset using the pipeline. Returns the Asset object."""
    from app.orchestrator import run_pipeline
    from app.schemas.orchestrator import PipelineRequest

    at = AssetType(asset_type) if asset_type in [e.value for e in AssetType] else AssetType.LANDING_PAGE
    mm = MonetizationModel(monetization) if monetization in [e.value for e in MonetizationModel] else MonetizationModel.AFFILIATES

    async with AsyncSessionLocal() as db:
        request = PipelineRequest(
            keyword=keyword,
            type=at,
            monetization_model=mm,
            async_mode=False,
        )
        asset = await run_pipeline(request, db)
        return asset


async def _create_blog_for_asset(keyword: str, sector: str, asset_id: int) -> Optional[BlogPost]:
    """Create a blog post related to the asset."""
    title = f"Guía Completa de {keyword.replace('-', ' ').title()} — Análisis y Recomendaciones"

    from app.routes.blog import _generate_blog_content, _slugify

    html, excerpt, meta = await _generate_blog_content(title, keyword, sector)
    slug = _slugify(title)

    async with AsyncSessionLocal() as db:
        # Check for duplicate slug
        exist = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
        if exist.scalar_one_or_none():
            slug = f"{slug}-{int(datetime.utcnow().timestamp()) % 10000}"

        post = BlogPost(
            title=title, slug=slug, excerpt=excerpt,
            content_html=html, meta_description=meta,
            focus_keyword=keyword, sector=sector,
            category=sector, status=BlogStatus.PUBLISHED,
            asset_id=asset_id, is_standalone=True,
            generated_by="agent", published_at=datetime.utcnow(),
            tags=json.dumps([keyword, sector]),
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post


async def analyze_keyword_intent(keyword: str) -> dict:
    """Deep analysis of a keyword's commercial intent and ROI potential."""
    from app.services.market_research import analyze_keyword_deep
    return await analyze_keyword_deep(keyword)
