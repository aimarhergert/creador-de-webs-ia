"""Blog system — standalone and asset-integrated blog posts."""

import json
import re
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.blog import BlogPost, BlogStatus
from app.services.ai_provider import generate_with_fallback

router = APIRouter()


class BlogCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    category: str | None = None
    sector: str | None = None
    focus_keyword: str | None = None
    tags: list[str] | None = None
    asset_id: int | None = None
    is_standalone: bool = False
    generate_content: bool = True


class BlogUpdate(BaseModel):
    title: str | None = None
    content_html: str | None = None
    excerpt: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    meta_description: str | None = None
    focus_keyword: str | None = None
    status: BlogStatus | None = None


class BlogOut(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: str | None
    content_html: str | None
    cover_image: str | None
    category: str | None
    tags: str | None
    sector: str | None
    status: str
    meta_title: str | None
    meta_description: str | None
    focus_keyword: str | None
    views: int
    seo_score: int | None
    asset_id: int | None
    is_standalone: bool
    generated_by: str | None
    published_at: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class BlogListOut(BaseModel):
    total: int
    items: list[BlogOut]


def _slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")[:200]


async def _generate_blog_content(title: str, keyword: str, sector: str) -> tuple[str, str, str]:
    """Generate blog HTML, excerpt, and meta description via AI."""
    prompt = f"""Escribe un artículo de blog profesional en español (HTML) sobre:

TÍTULO: {title}
KEYWORD PRINCIPAL: {keyword}
SECTOR: {sector}

El artículo debe incluir:
- Un <h1> con el título
- Una introducción atractiva
- 3-4 secciones con <h2>
- Datos, estadísticas o ejemplos concretos
- Una conclusión con call-to-action
- Entre 800-1500 palabras
- Meta descripción de 140-160 chars

Formatea el contenido en HTML limpio (sin <!DOCTYPE>, sin <head>, solo el <article>).
Usa clases CSS: prose, prose-h2:text-blue-400, etc.

Responde en JSON:
{{
  "html": "<article>...</article>",
  "excerpt": "breve resumen de 2 frases",
  "meta_description": "descripción SEO de 140-160 caracteres"
}}"""

    try:
        resp = await generate_with_fallback(prompt, max_tokens=2000, temperature=0.7)
        # Parse JSON from response
        text = resp.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        data = json.loads(text)
        return data.get("html", ""), data.get("excerpt", ""), data.get("meta_description", "")
    except Exception:
        # Fallback: generate simple HTML
        html = f"""<article>
<h1>{title}</h1>
<p><em>Publicado por AROS · Lectura de 5 min</em></p>
<p>Bienvenido a nuestro análisis sobre <strong>{keyword}</strong>. En este artículo exploramos los aspectos más relevantes del sector {sector}.</p>
<h2>Introducción</h2>
<p>El mercado relacionado con {keyword} está en constante evolución. Cada día surgen nuevas tendencias y oportunidades que los inversores inteligentes deben conocer.</p>
<h2>Análisis del Mercado</h2>
<p>Los datos más recientes indican un crecimiento sostenido en el sector {sector}, con una demanda creciente de contenido de calidad sobre {keyword}.</p>
<h2>Oportunidades de Inversión</h2>
<p>Invertir en contenido relacionado con {keyword} ofrece un ROI potencial elevado debido a la baja competencia y el alto volumen de búsquedas.</p>
<h2>Conclusión</h2>
<p>{keyword} representa una oportunidad real para generar ingresos pasivos mediante contenido optimizado. AROS puede ayudarte a capitalizar esta tendencia automáticamente.</p>
</article>"""
        excerpt = f"Análisis completo sobre {keyword} en el sector {sector}. Descubre las oportunidades de inversión y las tendencias del mercado."
        meta = f"Guía completa de {keyword}. Análisis, tendencias y oportunidades de inversión en el sector {sector}. Entra y descubre más."
        return html, excerpt, meta


# ── Routes ──────────────────────────────────────────────────────────────────

@router.get("", response_model=BlogListOut)
async def list_posts(
    limit: int = Query(default=20, le=100),
    status: BlogStatus | None = None,
    category: str | None = None,
    sector: str | None = None,
    standalone_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(BlogPost)
    if status:
        query = query.where(BlogPost.status == status)
    if category:
        query = query.where(BlogPost.category == category)
    if sector:
        query = query.where(BlogPost.sector == sector)
    if standalone_only:
        query = query.where(BlogPost.is_standalone == True)

    count = await db.execute(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.order_by(desc(BlogPost.created_at)).limit(limit))
    posts = result.scalars().all()

    return BlogListOut(total=count.scalar(), items=[BlogOut(
        id=p.id, title=p.title, slug=p.slug, excerpt=p.excerpt,
        content_html=p.content_html, cover_image=p.cover_image,
        category=p.category, tags=p.tags, sector=p.sector,
        status=p.status.value if p.status else "draft",
        meta_title=p.meta_title, meta_description=p.meta_description,
        focus_keyword=p.focus_keyword, views=p.views, seo_score=p.seo_score,
        asset_id=p.asset_id, is_standalone=p.is_standalone,
        generated_by=p.generated_by,
        published_at=p.published_at.isoformat() if p.published_at else None,
        created_at=p.created_at.isoformat() if p.created_at else "",
        updated_at=p.updated_at.isoformat() if p.updated_at else "",
    ) for p in posts])


@router.get("/{post_id}", response_model=BlogOut)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    return BlogOut(
        id=p.id, title=p.title, slug=p.slug, excerpt=p.excerpt,
        content_html=p.content_html, cover_image=p.cover_image,
        category=p.category, tags=p.tags, sector=p.sector,
        status=p.status.value if p.status else "draft",
        meta_title=p.meta_title, meta_description=p.meta_description,
        focus_keyword=p.focus_keyword, views=p.views, seo_score=p.seo_score,
        asset_id=p.asset_id, is_standalone=p.is_standalone,
        generated_by=p.generated_by,
        published_at=p.published_at.isoformat() if p.published_at else None,
        created_at=p.created_at.isoformat() if p.created_at else "",
        updated_at=p.updated_at.isoformat() if p.updated_at else "",
    )


@router.post("", response_model=BlogOut, status_code=201)
async def create_post(
    body: BlogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    slug = _slugify(body.title)

    # Check duplicate slug
    exist = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    if exist.scalar_one_or_none():
        slug = f"{slug}-{int(__import__('time').time()) % 10000}"

    post = BlogPost(
        title=body.title, slug=slug,
        category=body.category, sector=body.sector,
        focus_keyword=body.focus_keyword,
        tags=json.dumps(body.tags) if body.tags else None,
        asset_id=body.asset_id,
        is_standalone=body.is_standalone,
        user_id=current_user.id,
        status=BlogStatus.DRAFT,
    )

    if body.generate_content:
        keyword = body.focus_keyword or body.title
        sector = body.sector or "general"
        html, excerpt, meta = await _generate_blog_content(body.title, keyword, sector)
        post.content_html = html
        post.excerpt = excerpt
        post.meta_description = meta or body.meta_description
        post.generated_by = "ai"

    db.add(post)
    await db.commit()
    await db.refresh(post)

    return BlogOut(
        id=post.id, title=post.title, slug=post.slug, excerpt=post.excerpt,
        content_html=post.content_html, cover_image=post.cover_image,
        category=post.category, tags=post.tags, sector=post.sector,
        status=post.status.value if post.status else "draft",
        meta_title=post.meta_title, meta_description=post.meta_description,
        focus_keyword=post.focus_keyword, views=post.views, seo_score=post.seo_score,
        asset_id=post.asset_id, is_standalone=post.is_standalone,
        generated_by=post.generated_by,
        published_at=post.published_at.isoformat() if post.published_at else None,
        created_at=post.created_at.isoformat() if post.created_at else "",
        updated_at=post.updated_at.isoformat() if post.updated_at else "",
    )


@router.patch("/{post_id}", response_model=BlogOut)
async def update_post(
    post_id: int,
    body: BlogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    update_data = body.model_dump(exclude_none=True)
    if "tags" in update_data and isinstance(update_data["tags"], list):
        update_data["tags"] = json.dumps(update_data["tags"])
    if "status" in update_data and isinstance(update_data["status"], BlogStatus):
        if body.status == BlogStatus.PUBLISHED and not post.published_at:
            from datetime import datetime
            post.published_at = datetime.utcnow()

    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)

    return BlogOut(
        id=post.id, title=post.title, slug=post.slug, excerpt=post.excerpt,
        content_html=post.content_html, cover_image=post.cover_image,
        category=post.category, tags=post.tags, sector=post.sector,
        status=post.status.value if post.status else "draft",
        meta_title=post.meta_title, meta_description=post.meta_description,
        focus_keyword=post.focus_keyword, views=post.views, seo_score=post.seo_score,
        asset_id=post.asset_id, is_standalone=post.is_standalone,
        generated_by=post.generated_by,
        published_at=post.published_at.isoformat() if post.published_at else None,
        created_at=post.created_at.isoformat() if post.created_at else "",
        updated_at=post.updated_at.isoformat() if post.updated_at else "",
    )


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    await db.delete(post)
    await db.commit()
