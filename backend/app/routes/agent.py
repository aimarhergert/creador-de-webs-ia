"""Autonomous Agent routes — market research + auto-creation API."""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.market_research import research_market, analyze_keyword_deep
from app.services.autonomous_agent import run_autonomous_agent, AgentRunResult

router = APIRouter()


class AgentRunRequest(BaseModel):
    sectors: list[str] | None = None
    max_assets: int = Field(default=3, ge=1, le=10)
    dry_run: bool = False


class OpportunityOut(BaseModel):
    keyword: str
    sector: str
    source: str
    search_volume_est: int
    competition: str
    cpc_estimate: float
    trend_direction: str
    opportunity_score: int
    why: str
    suggested_asset_type: str
    suggested_monetization: str


class MarketReportOut(BaseModel):
    searched_at: str
    total_keywords_found: int
    sectors_analyzed: list[str]
    top_opportunities: list[OpportunityOut]
    ai_verdict: str
    recommended_action: str


class AgentRunOut(BaseModel):
    started_at: str
    keywords_found: int
    opportunities_analyzed: int
    assets_created: int
    blog_posts_created: int
    errors: list[str]
    created_asset_ids: list[int]
    top_keyword: str
    ai_verdict: str = ""


@router.get("/research", response_model=MarketReportOut)
async def agent_research(
    sectors: str | None = Query(default=None, description="Comma-separated: tech,health,finance"),
    deep: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Research the market — find trending keywords, score opportunities."""
    sector_list = [s.strip() for s in sectors.split(",")] if sectors else None
    report = await research_market(sectors=sector_list, deep=deep)

    return MarketReportOut(
        searched_at=report.searched_at.isoformat(),
        total_keywords_found=report.total_keywords_found,
        sectors_analyzed=report.sectors_analyzed,
        top_opportunities=[
            OpportunityOut(
                keyword=o.keyword, sector=o.sector, source=o.source,
                search_volume_est=o.search_volume_est,
                competition=o.competition, cpc_estimate=o.cpc_estimate,
                trend_direction=o.trend_direction,
                opportunity_score=o.opportunity_score,
                why=o.why,
                suggested_asset_type=o.suggested_asset_type,
                suggested_monetization=o.suggested_monetization,
            ) for o in report.top_opportunities
        ],
        ai_verdict=report.ai_verdict,
        recommended_action=report.recommended_action,
    )


@router.post("/run", response_model=AgentRunOut)
async def agent_run(
    body: AgentRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the autonomous agent: research + create assets automatically."""
    result = await run_autonomous_agent(
        sectors=body.sectors,
        max_assets=body.max_assets,
        dry_run=body.dry_run,
    )

    return AgentRunOut(
        started_at=result.started_at.isoformat(),
        keywords_found=result.keywords_found,
        opportunities_analyzed=result.opportunities_analyzed,
        assets_created=result.assets_created,
        blog_posts_created=result.blog_posts_created,
        errors=result.errors,
        created_asset_ids=result.created_asset_ids,
        top_keyword=result.top_keyword,
        ai_verdict=result.market_report.ai_verdict if result.market_report else "",
    )


@router.get("/analyze-keyword")
async def agent_analyze_keyword(
    keyword: str = Query(..., min_length=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deep-dive analysis of a single keyword."""
    return await analyze_keyword_deep(keyword)
