"""External Website Scanner routes."""

import json
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.scan import WebScan
from app.services.web_scanner import scan_website, ScanResult

router = APIRouter()


class ScanRequest(BaseModel):
    url: str
    deep_analysis: bool = True


class ScanOut(BaseModel):
    id: int
    url: str
    domain: str
    status_code: int
    seo_score: int
    content_score: int
    word_count: int
    title: str | None
    meta_description: str | None
    title_length: int = 0
    meta_length: int = 0
    h1_count: int = 0
    h2_count: int = 0
    internal_links: int = 0
    external_links: int = 0
    image_count: int = 0
    images_with_alt: int = 0
    has_schema: bool = False
    has_og_tags: bool = False
    has_mobile_viewport: bool = False
    load_time_ms: int = 0
    readability_score: float = 0.0
    sentiment: str = ""
    top_keywords: str | None
    estimated_traffic: int
    estimated_cpc: float
    content_type: str | None
    ai_insights: str | None
    recommendations: str | None
    error: str | None
    created_at: str

    model_config = {"from_attributes": True}


def _parse_scan_seo(scan: WebScan) -> dict:
    """Extract SEO detail fields from raw_data JSON."""
    defaults = {
        "title_length": len(scan.title or ""),
        "meta_length": len(scan.meta_description or ""),
        "h1_count": 0, "h2_count": 0, "internal_links": 0,
        "external_links": 0, "image_count": 0, "images_with_alt": 0,
        "has_schema": False, "has_og_tags": False, "has_mobile_viewport": False,
        "load_time_ms": 0, "readability_score": 0.0, "sentiment": "",
    }
    if scan.raw_data:
        try:
            raw = json.loads(scan.raw_data)
            seo_data = raw.get("seo", {})
            content_data = raw.get("content", {})
            defaults.update({k: seo_data.get(k, defaults[k]) for k in [
                "title_length", "h1_count", "h2_count", "internal_links",
                "external_links", "image_count", "images_with_alt",
                "has_schema", "has_og_tags", "has_mobile_viewport", "load_time_ms",
            ]})
            defaults["meta_length"] = len(scan.meta_description or "")
            defaults["readability_score"] = content_data.get("readability_score", 0.0)
            defaults["sentiment"] = content_data.get("sentiment", "")
        except (json.JSONDecodeError, TypeError):
            pass
    return defaults


def _scan_to_out(scan: WebScan) -> ScanOut:
    seo = _parse_scan_seo(scan)
    return ScanOut(
        id=scan.id, url=scan.url, domain=scan.domain,
        status_code=scan.status_code, seo_score=scan.seo_score,
        content_score=scan.content_score, word_count=scan.word_count,
        title=scan.title, meta_description=scan.meta_description,
        title_length=seo["title_length"], meta_length=seo["meta_length"],
        h1_count=seo["h1_count"], h2_count=seo["h2_count"],
        internal_links=seo["internal_links"], external_links=seo["external_links"],
        image_count=seo["image_count"], images_with_alt=seo["images_with_alt"],
        has_schema=seo["has_schema"], has_og_tags=seo["has_og_tags"],
        has_mobile_viewport=seo["has_mobile_viewport"], load_time_ms=seo["load_time_ms"],
        readability_score=seo["readability_score"], sentiment=seo["sentiment"],
        top_keywords=scan.top_keywords,
        estimated_traffic=scan.estimated_traffic,
        estimated_cpc=scan.estimated_cpc,
        content_type=scan.content_type,
        ai_insights=scan.ai_insights,
        recommendations=scan.recommendations,
        error=scan.error,
        created_at=scan.created_at.isoformat() if scan.created_at else "",
    )
    total: int
    items: list[ScanOut]



@router.post("/analyze", response_model=ScanFullOut)
async def analyze_url(
    body: ScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze an external website for SEO, content, and market intelligence."""
    if not body.url.startswith("http"):
        body.url = f"https://{body.url}"

    # Run scan
    result = await scan_website(body.url, deep_analysis=body.deep_analysis)

    # Persist
    from app.services.web_scanner import persist_scan
    scan_id = await persist_scan(body.url, result)

    # Return
    scan_result = await db.execute(select(WebScan).where(WebScan.id == scan_id))
    scan = scan_result.scalar_one()
    seo = _parse_scan_seo(scan)

    return ScanFullOut(
        id=scan.id, url=scan.url, domain=scan.domain,
        status_code=scan.status_code, seo_score=scan.seo_score,
        content_score=scan.content_score, word_count=scan.word_count,
        title=scan.title, meta_description=scan.meta_description,
        title_length=seo["title_length"], meta_length=seo["meta_length"],
        h1_count=seo["h1_count"], h2_count=seo["h2_count"],
        internal_links=seo["internal_links"], external_links=seo["external_links"],
        image_count=seo["image_count"], images_with_alt=seo["images_with_alt"],
        has_schema=seo["has_schema"], has_og_tags=seo["has_og_tags"],
        has_mobile_viewport=seo["has_mobile_viewport"], load_time_ms=seo["load_time_ms"],
        readability_score=seo["readability_score"], sentiment=seo["sentiment"],
        top_keywords=scan.top_keywords,
        estimated_traffic=scan.estimated_traffic,
        estimated_cpc=scan.estimated_cpc,
        content_type=scan.content_type,
        ai_insights=scan.ai_insights,
        recommendations=scan.recommendations,
        raw_data=scan.raw_data,
        error=scan.error,
        created_at=scan.created_at.isoformat() if scan.created_at else "",
    )


class ScanListOut(BaseModel):
    total: int
    items: list[ScanOut]


class ScanFullOut(ScanOut):
    raw_data: str | None = None

    model_config = {"from_attributes": True}



@router.get("/history", response_model=ScanListOut)
async def list_scans(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count_q = await db.execute(select(func.count()).select_from(WebScan))
    total = count_q.scalar()

    result = await db.execute(
        select(WebScan).order_by(desc(WebScan.created_at)).limit(limit)
    )
    scans = result.scalars().all()

    return ScanListOut(
        total=total,
        items=[_scan_to_out(s) for s in scans]
    )


@router.get("/history/{scan_id}", response_model=ScanFullOut)
async def get_scan(scan_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(WebScan).where(WebScan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Escaneo no encontrado")
    seo = _parse_scan_seo(scan)
    return ScanFullOut(
        id=scan.id, url=scan.url, domain=scan.domain,
        status_code=scan.status_code, seo_score=scan.seo_score,
        content_score=scan.content_score, word_count=scan.word_count,
        title=scan.title, meta_description=scan.meta_description,
        title_length=seo["title_length"], meta_length=seo["meta_length"],
        h1_count=seo["h1_count"], h2_count=seo["h2_count"],
        internal_links=seo["internal_links"], external_links=seo["external_links"],
        image_count=seo["image_count"], images_with_alt=seo["images_with_alt"],
        has_schema=seo["has_schema"], has_og_tags=seo["has_og_tags"],
        has_mobile_viewport=seo["has_mobile_viewport"], load_time_ms=seo["load_time_ms"],
        readability_score=seo["readability_score"], sentiment=seo["sentiment"],
        top_keywords=scan.top_keywords,
        estimated_traffic=scan.estimated_traffic,
        estimated_cpc=scan.estimated_cpc,
        content_type=scan.content_type,
        ai_insights=scan.ai_insights,
        recommendations=scan.recommendations,
        raw_data=scan.raw_data,
        error=scan.error,
        created_at=scan.created_at.isoformat() if scan.created_at else "",
    )
