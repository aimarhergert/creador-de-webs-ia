"""
Enterprise Asset Factory v2 — multi-page premium website generation.

Generation pipeline (9 API calls, 4 phases):
  Phase 0 (sequential): Site plan JSON — content, SEO copy, blog outlines, colors
  Phase 1 (parallel ×3): index.html + styles.css + scripts.js
  Phase 2 (parallel ×3): post-1.html + post-2.html + post-3.html
  Phase 3 (parallel ×2): blog.html + contact.html

Output (8 files):
  index.html, blog.html, post-1.html, post-2.html, post-3.html,
  contact.html, styles.css, scripts.js
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import anthropic
from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.asset import Asset, AssetType, AssetStatus, MonetizationModel
from app.services.monetization_engine import inject_tracking_pixel

logger = logging.getLogger(__name__)

_client: Optional[AsyncAnthropic] = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY no está configurada")
        _client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


# ─────────────────────────────────────────────────────────────────────────────
# Site Plan Dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BlogPost:
    title: str
    slug: str
    meta_desc: str
    hero_unsplash_id: str
    section_headings: list[str]     # 4 H2 titles
    h3_per_section: list[list[str]] # H3 titles per section

    @property
    def filename(self) -> str:
        return f"{self.slug}.html"


@dataclass
class SitePlan:
    keyword: str
    lang: str
    brand: str
    tagline: str
    accent: str            # color accent: "emerald" | "violet" | "amber" | "sky"
    accent_hex: str        # e.g. "#10b981"
    hero_headline: str
    hero_subheadline: str
    hero_cta_primary: str
    hero_cta_secondary: str
    hero_unsplash_id: str
    stats: list[dict]      # [{value, label}]
    features: list[dict]   # [{icon, title, desc}]
    testimonials: list[dict]  # [{name, role, company, quote, unsplash_id}]
    faq: list[dict]        # [{q, a}]
    blog_posts: list[BlogPost]
    contact_email: str
    footer_tagline: str
    meta_title: str
    meta_desc: str
    monetization: MonetizationModel
    asset_type: AssetType


# ─────────────────────────────────────────────────────────────────────────────
# Streaming primitive (shared by all file generators)
# ─────────────────────────────────────────────────────────────────────────────

async def _stream_file(
    system: str,
    user: str,
    max_tokens: int = 8192,
    label: str = "file",
    max_retries: int = 3,
) -> str:
    client = _get_client()
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[AssetFactory] Streaming {label} — attempt {attempt}/{max_retries}")
            async with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            ) as stream:
                text = await stream.get_final_text()
                final = await stream.get_final_message()

            if final.stop_reason == "max_tokens":
                logger.warning(f"[AssetFactory] {label} hit max_tokens — may be truncated")

            logger.info(
                f"[AssetFactory] {label} done — "
                f"{final.usage.output_tokens} tokens, {len(text):,} chars"
            )
            # Strip markdown fences if model adds them anyway
            text = re.sub(r"^```[\w]*\n?", "", text.strip())
            text = re.sub(r"\n?```$", "", text)
            return text.strip()

        except anthropic.RateLimitError:
            wait = 2 ** (attempt - 1) * 12
            if attempt < max_retries:
                logger.warning(f"[AssetFactory] Rate limit — retrying {label} in {wait}s")
                await asyncio.sleep(wait)
            else:
                raise
        except anthropic.AuthenticationError:
            logger.error("[AssetFactory] Invalid ANTHROPIC_API_KEY")
            raise
        except anthropic.APIStatusError as exc:
            logger.error(f"[AssetFactory] API {exc.status_code}: {exc.message}")
            if exc.status_code >= 500 and attempt < max_retries:
                await asyncio.sleep(5 * attempt)
                continue
            raise

    raise RuntimeError(f"[AssetFactory] {label} failed after {max_retries} retries")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 0 — Site Plan
# ─────────────────────────────────────────────────────────────────────────────

_PLAN_SYSTEM = """\
You are a senior content strategist and SEO architect.
Produce a compact site plan JSON. Output ONLY valid JSON — no markdown, no fences, no explanation.
Keep values SHORT — the content generators will expand them into full copy.

Schema (follow EXACTLY, do not add extra fields):
{
  "lang": "es",
  "brand": "Brand Name",
  "tagline": "Short tagline",
  "accent": "emerald",
  "accent_hex": "#10b981",
  "hero_headline": "Headline 6-10 words",
  "hero_subheadline": "Subheadline 15-20 words",
  "hero_cta_primary": "CTA text",
  "hero_cta_secondary": "Secondary CTA",
  "hero_unsplash_id": "1488590528505-98d2b5aba04b",
  "stats": [
    {"value": "10K+", "label": "Short label"},
    {"value": "98%", "label": "Short label"},
    {"value": "4.9/5", "label": "Short label"},
    {"value": "24/7", "label": "Short label"}
  ],
  "features": [
    {"icon": "🚀", "title": "Short title", "desc": "One sentence max."},
    {"icon": "🎯", "title": "Short title", "desc": "One sentence max."},
    {"icon": "💡", "title": "Short title", "desc": "One sentence max."},
    {"icon": "🔒", "title": "Short title", "desc": "One sentence max."},
    {"icon": "📈", "title": "Short title", "desc": "One sentence max."},
    {"icon": "⚡", "title": "Short title", "desc": "One sentence max."}
  ],
  "testimonials": [
    {"name": "Full Name", "role": "Job Title", "company": "Company", "quote": "One sentence quote.", "unsplash_id": "1494790108377-be9c29b29330"},
    {"name": "Full Name", "role": "Job Title", "company": "Company", "quote": "One sentence quote.", "unsplash_id": "1507003211169-0a1dd7228f2d"},
    {"name": "Full Name", "role": "Job Title", "company": "Company", "quote": "One sentence quote.", "unsplash_id": "1438761681033-6461ffad8d80"}
  ],
  "faq": [
    {"q": "Question 1?", "a": "Brief answer 1-2 sentences."},
    {"q": "Question 2?", "a": "Brief answer 1-2 sentences."},
    {"q": "Question 3?", "a": "Brief answer 1-2 sentences."},
    {"q": "Question 4?", "a": "Brief answer 1-2 sentences."},
    {"q": "Question 5?", "a": "Brief answer 1-2 sentences."},
    {"q": "Question 6?", "a": "Brief answer 1-2 sentences."}
  ],
  "blog_posts": [
    {
      "title": "SEO article title with main keyword",
      "slug": "post-1",
      "meta_desc": "Max 155 chars description.",
      "hero_unsplash_id": "1488590528505-98d2b5aba04b",
      "section_headings": ["H2 title 1", "H2 title 2", "H2 title 3", "H2 title 4"],
      "h3_per_section": [["H3 a", "H3 b"], ["H3 c"], ["H3 d", "H3 e"], []]
    },
    {
      "title": "Second article title",
      "slug": "post-2",
      "meta_desc": "Max 155 chars description.",
      "hero_unsplash_id": "1518770055-fe5e233b75c7",
      "section_headings": ["H2 title 1", "H2 title 2", "H2 title 3", "H2 title 4"],
      "h3_per_section": [[], ["H3 a", "H3 b"], ["H3 c"], []]
    },
    {
      "title": "Third article title",
      "slug": "post-3",
      "meta_desc": "Max 155 chars description.",
      "hero_unsplash_id": "1551288049-bebba4ee19c5",
      "section_headings": ["H2 title 1", "H2 title 2", "H2 title 3", "H2 title 4"],
      "h3_per_section": [["H3 a"], [], ["H3 b", "H3 c"], []]
    }
  ],
  "contact_email": "info@brand.com",
  "footer_tagline": "Short tagline",
  "meta_title": "Homepage title 50-60 chars",
  "meta_desc": "Homepage meta 150-160 chars"
}

RULES:
- ALL copy in the SAME LANGUAGE as the input keyword
- accent: "emerald" / "violet" / "amber" / "sky" — pick most fitting for the niche
- 3 blog posts on distinct subtopics of the main keyword
- section_headings: exactly 4 items per post (concise H2 titles)
- h3_per_section: array of arrays matching section_headings length
- Keep ALL values SHORT — generators expand the content
- Valid Unsplash photo IDs only (pick topic-relevant IDs you know exist)\
"""


async def _generate_site_plan(
    keyword: str,
    asset_type: AssetType,
    monetization: MonetizationModel,
) -> SitePlan:
    logger.info(f"[AssetFactory] Phase 0: Planning site for '{keyword}'")

    mon_hint = {
        MonetizationModel.AFFILIATES: "Include affiliate product recommendations naturally in features and CTAs.",
        MonetizationModel.ADS: "Structure content with clear ad placement zones between sections.",
        MonetizationModel.ECOMMERCE: "Focus on product benefits, pricing psychology, and purchase CTAs.",
        MonetizationModel.LEADS: "Emphasize lead capture: free guides, consultations, demos.",
        MonetizationModel.NONE: "",
    }.get(monetization, "")

    type_hint = {
        AssetType.BLOG: "This is a content/blog site — optimize for informational intent and reader engagement.",
        AssetType.ECOMMERCE: "This is an ecommerce site — optimize for transactional intent and purchases.",
        AssetType.LEAD_GEN: "This is a lead gen site — optimize for capturing contact information.",
        AssetType.LANDING_PAGE: "This is a conversion landing page — optimize for immediate action.",
    }.get(asset_type, "")

    raw = await _stream_file(
        system=_PLAN_SYSTEM,
        user=(
            f'Create a COMPACT site plan JSON for: "{keyword}"\n'
            f'Site type: {type_hint}\n'
            f'Monetization: {mon_hint}\n'
            'ALL text values must be SHORT (1 sentence max per field — generators expand content).\n'
            'Output ONLY valid JSON. No markdown. No code fences.'
        ),
        max_tokens=4000,
        label="site_plan",
    )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Extract JSON from response if model added preamble
        match = re.search(r"\{[\s\S]+\}", raw)
        if match:
            data = json.loads(match.group())
        else:
            raise ValueError(f"[AssetFactory] Site plan JSON parse failed. Raw: {raw[:300]}")

    blog_posts = [
        BlogPost(
            title=p["title"],
            slug=p["slug"],
            meta_desc=p["meta_desc"],
            hero_unsplash_id=p.get("hero_unsplash_id", "1488590528505-98d2b5aba04b"),
            section_headings=p.get("section_headings", ["Introducción", "Desarrollo", "Conclusiones", "Resumen"]),
            h3_per_section=p.get("h3_per_section", [[], [], [], []]),
        )
        for p in data.get("blog_posts", [])
    ]

    plan = SitePlan(
        keyword=keyword,
        lang=data.get("lang", "es"),
        brand=data.get("brand", keyword.title()),
        tagline=data.get("tagline", ""),
        accent=data.get("accent", "emerald"),
        accent_hex=data.get("accent_hex", "#10b981"),
        hero_headline=data.get("hero_headline", keyword),
        hero_subheadline=data.get("hero_subheadline", ""),
        hero_cta_primary=data.get("hero_cta_primary", "Empezar ahora"),
        hero_cta_secondary=data.get("hero_cta_secondary", "Saber más"),
        hero_unsplash_id=data.get("hero_unsplash_id", "1488590528505-98d2b5aba04b"),
        stats=data.get("stats", []),
        features=data.get("features", []),
        testimonials=data.get("testimonials", []),
        faq=data.get("faq", []),
        blog_posts=blog_posts,
        contact_email=data.get("contact_email", f"info@{keyword.split()[0].lower()}.com"),
        footer_tagline=data.get("footer_tagline", ""),
        meta_title=data.get("meta_title", keyword),
        meta_desc=data.get("meta_desc", ""),
        monetization=monetization,
        asset_type=asset_type,
    )
    logger.info(
        f"[AssetFactory] Plan ready — brand='{plan.brand}', lang={plan.lang}, "
        f"accent={plan.accent}, posts={len(plan.blog_posts)}"
    )
    return plan


# ─────────────────────────────────────────────────────────────────────────────
# Shared HTML skeleton helpers
# ─────────────────────────────────────────────────────────────────────────────

_TAILWIND_ACCENT_MAP = {
    "emerald": ("emerald", "#10b981", "#34d399", "#065f46"),
    "violet":  ("violet",  "#8b5cf6", "#a78bfa", "#4c1d95"),
    "amber":   ("amber",   "#f59e0b", "#fcd34d", "#78350f"),
    "sky":     ("sky",     "#0ea5e9", "#38bdf8", "#0c4a6e"),
}

def _accent_classes(plan: SitePlan) -> dict:
    name = plan.accent if plan.accent in _TAILWIND_ACCENT_MAP else "emerald"
    _, base, light, dark = _TAILWIND_ACCENT_MAP[name]
    return {
        "name": name,
        "btn_primary": f"bg-{name}-500 hover:bg-{name}-400 text-slate-950",
        "btn_secondary": f"border border-{name}-500/40 hover:border-{name}-400 text-{name}-300",
        "text": f"text-{name}-400",
        "text_light": f"text-{name}-300",
        "border": f"border-{name}-500/30",
        "glow": f"shadow-{name}-500/20",
        "gradient": f"from-{name}-400 to-{name}-300",
        "bg_subtle": f"bg-{name}-500/10",
        "base": base,
        "light": light,
        "dark": dark,
    }


def _shared_head(plan: SitePlan, title: str, desc: str, canonical: str = "") -> str:
    a = _accent_classes(plan)
    return f"""<!DOCTYPE html>
<html lang="{plan.lang}" class="scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#020617">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="robots" content="index, follow">
  {f'<link rel="canonical" href="{canonical}">' if canonical else ''}

  <!-- OpenGraph -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="https://images.unsplash.com/photo-{plan.hero_unsplash_id}?auto=format&fit=crop&q=80&w=1200&h=630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&display=swap" rel="stylesheet">

  <!-- Tailwind CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['Inter', 'system-ui', 'sans-serif'],
            serif: ['Playfair Display', 'Georgia', 'serif'],
          }},
          colors: {{
            accent: {{
              50: '{a["light"]}15',
              100: '{a["light"]}25',
              400: '{a["light"]}',
              500: '{a["base"]}',
              600: '{a["dark"]}',
            }},
          }},
          animation: {{
            'fade-up': 'fadeUp 0.6s ease forwards',
            'fade-in': 'fadeIn 0.5s ease forwards',
            'float': 'float 6s ease-in-out infinite',
          }},
        }},
      }},
    }}
  </script>

  <!-- Custom styles -->
  <link rel="stylesheet" href="styles.css">
</head>"""


def _shared_navbar(plan: SitePlan, current: str = "home") -> str:
    a = _accent_classes(plan)
    nav_items = [
        ("Inicio", "index.html", "home"),
        ("Blog", "blog.html", "blog"),
        ("Contacto", "contact.html", "contact"),
    ]
    items_html = ""
    for label, href, key in nav_items:
        active = 'class="text-white"' if key == current else f'class="text-slate-400 hover:text-white transition-colors"'
        items_html += f'<a href="{href}" {active}>{label}</a>\n'

    return f"""  <!-- NAVBAR -->
  <nav id="navbar" class="fixed top-0 left-0 right-0 z-50 transition-all duration-300" aria-label="Main navigation">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16 lg:h-20">
        <!-- Logo -->
        <a href="index.html" class="flex items-center gap-3 group">
          <div class="w-9 h-9 rounded-xl bg-accent-500 flex items-center justify-center shadow-lg shadow-accent-500/25 group-hover:scale-110 transition-transform">
            <span class="text-slate-950 font-black text-sm">{plan.brand[0].upper()}</span>
          </div>
          <span class="font-bold text-white text-lg tracking-tight">{plan.brand}</span>
        </a>

        <!-- Desktop nav -->
        <div class="hidden md:flex items-center gap-8 text-sm font-medium">
          {items_html}
        </div>

        <!-- CTA + Mobile toggle -->
        <div class="flex items-center gap-3">
          <a href="contact.html"
            class="hidden md:inline-flex items-center gap-2 {a["btn_primary"]} text-sm font-semibold rounded-xl px-5 py-2.5 transition-all hover:scale-105 shadow-lg shadow-accent-500/20">
            {plan.hero_cta_primary}
          </a>
          <button id="mobile-menu-btn" aria-label="Open menu"
            class="md:hidden w-10 h-10 flex items-center justify-center rounded-xl border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 transition-colors">
            <svg id="menu-icon-open" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
            <svg id="menu-icon-close" class="w-5 h-5 hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile menu -->
    <div id="mobile-menu" class="hidden md:hidden bg-slate-900/95 backdrop-blur-xl border-t border-slate-800">
      <div class="px-4 py-4 space-y-1">
        {chr(10).join(f'<a href="{href}" class="block px-4 py-3 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors">{label}</a>' for label, href, _ in nav_items)}
        <a href="contact.html" class="block mt-2 text-center {a["btn_primary"]} text-sm font-semibold rounded-xl px-5 py-3 transition-colors">
          {plan.hero_cta_primary}
        </a>
      </div>
    </div>
  </nav>"""


def _shared_footer(plan: SitePlan) -> str:
    a = _accent_classes(plan)
    year = datetime.now().year
    posts_links = "\n".join(
        f'<li><a href="{p.filename}" class="text-slate-500 hover:text-slate-300 transition-colors text-sm">{p.title[:55]}{"…" if len(p.title) > 55 else ""}</a></li>'
        for p in plan.blog_posts
    )
    return f"""  <!-- FOOTER -->
  <footer class="bg-slate-950 border-t border-slate-800/50 pt-16 pb-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-12">
        <!-- Brand -->
        <div class="lg:col-span-2">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-9 h-9 rounded-xl bg-accent-500 flex items-center justify-center">
              <span class="text-slate-950 font-black text-sm">{plan.brand[0].upper()}</span>
            </div>
            <span class="font-bold text-white text-lg">{plan.brand}</span>
          </div>
          <p class="text-slate-500 text-sm leading-relaxed max-w-sm mb-5">{plan.footer_tagline}</p>
          <!-- Social icons -->
          <div class="flex items-center gap-3">
            <a href="#" aria-label="Twitter" class="w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.748l7.73-8.835L1.254 2.25H8.08l4.26 5.632zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            </a>
            <a href="#" aria-label="LinkedIn" class="w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
            </a>
            <a href="#" aria-label="Instagram" class="w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
            </a>
          </div>
        </div>

        <!-- Navigation -->
        <div>
          <h3 class="text-white font-semibold text-sm uppercase tracking-wider mb-4">Navegación</h3>
          <ul class="space-y-2.5">
            <li><a href="index.html" class="text-slate-500 hover:text-slate-300 transition-colors text-sm">Inicio</a></li>
            <li><a href="blog.html" class="text-slate-500 hover:text-slate-300 transition-colors text-sm">Blog</a></li>
            <li><a href="contact.html" class="text-slate-500 hover:text-slate-300 transition-colors text-sm">Contacto</a></li>
          </ul>
        </div>

        <!-- Latest posts -->
        <div>
          <h3 class="text-white font-semibold text-sm uppercase tracking-wider mb-4">Artículos recientes</h3>
          <ul class="space-y-2.5">
            {posts_links}
          </ul>
        </div>
      </div>

      <!-- Bottom bar -->
      <div class="pt-8 border-t border-slate-800/50 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p class="text-slate-600 text-xs">© {year} {plan.brand}. Todos los derechos reservados.</p>
        <div class="flex items-center gap-5 text-xs text-slate-600">
          <a href="#" class="hover:text-slate-400 transition-colors">Privacidad</a>
          <a href="#" class="hover:text-slate-400 transition-colors">Términos</a>
          <a href="#" class="hover:text-slate-400 transition-colors">Cookies</a>
        </div>
      </div>
    </div>
  </footer>"""


# ─────────────────────────────────────────────────────────────────────────────
# Monetization hint builders (injected into prompts)
# ─────────────────────────────────────────────────────────────────────────────

def _mon_html_hint(plan: SitePlan) -> str:
    if plan.monetization == MonetizationModel.AFFILIATES:
        return (
            "Include 3-4 prominent affiliate CTA buttons with data-affiliate='true', "
            "text like 'Ver mejor precio →' or 'Comparar ofertas →', "
            "styled with the accent color. Place them in the hero, features, and CTA sections."
        )
    if plan.monetization == MonetizationModel.ADS:
        return (
            "Include <div class='ad-slot ad-slot--top' data-ad-unit='top-banner'></div> "
            "between the hero and features, and <div class='ad-slot ad-slot--mid' data-ad-unit='mid-content'></div> "
            "between features and testimonials."
        )
    if plan.monetization == MonetizationModel.ECOMMERCE:
        return (
            "Add a premium product showcase section with 3 product cards: "
            "each has image, name, price (styled with accent), and "
            "'Comprar ahora' button with data-stripe-checkout='true'."
        )
    if plan.monetization == MonetizationModel.LEADS:
        return (
            "Include a prominent lead capture section after testimonials: "
            "offer a free guide/consultation, form with name + email + phone fields, "
            "and a large submit button. Style it as a high-contrast section."
        )
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — index.html
# ─────────────────────────────────────────────────────────────────────────────

_HTML_SYSTEM = """\
You are a senior front-end engineer and conversion specialist at a top-tier digital agency.
Generate ONLY raw HTML — no markdown fences, no explanations, no comments about what you're doing.
Start with <!DOCTYPE html> and end with </html>.

TECHNICAL REQUIREMENTS (non-negotiable):
1. Use the EXACT <head> block provided — do not modify it
2. Include <link rel="stylesheet" href="styles.css"> in head
3. Include <script src="scripts.js"></script> just before </body>
4. All interactive elements must have appropriate IDs/classes for scripts.js to hook into
5. Use semantic HTML5 (header, nav, main, section, article, footer, aside)
6. Every section needs: id attribute + data-animate="fade-up" for scroll animations

DESIGN LANGUAGE (enforce strictly):
- Background: bg-slate-950 for page, bg-slate-900 for cards/panels
- Text hierarchy: text-white (titles) → text-slate-300 (body) → text-slate-500 (captions)
- Cards: bg-slate-900 border border-slate-700/50 rounded-2xl p-6 hover:border-slate-600/50 transition-all
- Accent color: use the accent CSS variable (--accent-color) via text-accent-500, bg-accent-500, border-accent-500
- Gradients on headlines: bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent
- Background grid: decorative dot/line grid pattern via CSS
- Glassmorphism panels: bg-white/5 backdrop-blur-md border border-white/10

SECTION REQUIREMENTS:
§1 STICKY NAVBAR — pre-built, use the exact navbar HTML provided
§2 HERO — full viewport height, centered content, large gradient headline (font-serif text-5xl md:text-7xl),
    subtitle, two CTA buttons (primary accent + secondary ghost),
    animated background grid + floating glow orbs (decorative divs with blur)
§3 STATS BAR — 4 impressive metrics in a grid, each with large number (font-mono text-4xl font-bold accent-colored) + label
§4 FEATURES — 2-column on tablet, 3-column on desktop grid,
    each card: icon (text-3xl) + title (font-semibold text-white) + desc (text-slate-400)
§5 SOCIAL PROOF / TESTIMONIALS — 3 cards in a grid, each:
    avatar img (rounded-full w-12 h-12 object-cover), name (font-semibold), role+company (text-slate-500 text-sm),
    quote (italic text-slate-300), 5 star icons (text-amber-400)
§6 FAQ ACCORDION — 6 questions, each as a <details> element OR use divs with class="faq-item" + data-faq,
    questions in font-medium text-white, answers in text-slate-400
§7 FINAL CTA SECTION — gradient background section, large headline, subtext, two action buttons
§8 FOOTER — pre-built, use the exact footer HTML provided

IMAGES: Use Unsplash URLs: https://images.unsplash.com/photo-{ID}?auto=format&fit=crop&q=80&w={W}&h={H}
For avatars use small images with w=96&h=96, for hero use w=1600&h=900\
"""


async def _gen_index(plan: SitePlan) -> str:
    a = _accent_classes(plan)
    head = _shared_head(plan, plan.meta_title, plan.meta_desc)
    navbar = _shared_navbar(plan, "home")
    footer = _shared_footer(plan)
    mon_hint = _mon_html_hint(plan)

    features_json = json.dumps(plan.features, ensure_ascii=False, indent=2)
    stats_json = json.dumps(plan.stats, ensure_ascii=False, indent=2)
    testimonials_json = json.dumps(plan.testimonials, ensure_ascii=False, indent=2)
    faq_json = json.dumps(plan.faq, ensure_ascii=False, indent=2)
    posts_json = json.dumps(
        [{"title": p.title, "slug": p.slug, "meta_desc": p.meta_desc} for p in plan.blog_posts],
        ensure_ascii=False, indent=2
    )

    user = f"""Build the complete index.html for:
Brand: {plan.brand}
Keyword/Niche: {plan.keyword}
Language: {plan.lang}
Accent: {a["name"]} (use classes like text-{a["name"]}-400, bg-{a["name"]}-500 etc.)

HERO:
  Headline: "{plan.hero_headline}"
  Subheadline: "{plan.hero_subheadline}"
  CTA primary: "{plan.hero_cta_primary}" → links to contact.html
  CTA secondary: "{plan.hero_cta_secondary}" → links to blog.html
  Hero image: https://images.unsplash.com/photo-{plan.hero_unsplash_id}?auto=format&fit=crop&q=80&w=1600&h=900

STATS: {stats_json}

FEATURES: {features_json}

TESTIMONIALS: {testimonials_json}

FAQ: {faq_json}

BLOG PREVIEW (show 3 post cards linking to their pages): {posts_json}

MONETIZATION: {mon_hint if mon_hint else "No specific monetization — focus on brand/authority."}

JSON-LD SCHEMA (include in <head>):
{{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "{plan.meta_title}",
  "description": "{plan.meta_desc}",
  "url": "index.html"
}}

EXACT HEAD BLOCK TO USE (copy verbatim, add JSON-LD before </head>):
{head}

EXACT NAVBAR TO USE (copy verbatim):
{navbar}

EXACT FOOTER TO USE (copy verbatim):
{footer}

Now generate the COMPLETE index.html. It must be visually stunning — agency quality.
Include ALL 8 sections. No placeholders, no TODO comments. Full content only."""

    html = await _stream_file(
        system=_HTML_SYSTEM,
        user=user,
        max_tokens=8192,
        label="index.html",
    )
    return _ensure_minimum_html(html, plan, "index.html")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — styles.css
# ─────────────────────────────────────────────────────────────────────────────

_CSS_SYSTEM = """\
You are a CSS expert. Output ONLY raw CSS — no markdown, no fences, no explanations.
This file complements Tailwind CSS. Write ONLY what Tailwind cannot express natively.\
"""


async def _gen_styles(plan: SitePlan) -> str:
    a = _accent_classes(plan)
    user = f"""Generate styles.css for the {plan.brand} site (keyword: "{plan.keyword}").
Accent color: {a["base"]} ({a["name"]})

REQUIRED RULES (write all of these):

:root {{
  --accent-color: {a["base"]};
  --accent-light: {a["light"]};
  --accent-dark: {a["dark"]};
  --bg-primary: #020617;
  --bg-secondary: #0f172a;
  --bg-card: #0f172a;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-serif: 'Playfair Display', Georgia, serif;
}}

SECTIONS TO INCLUDE:
1. CSS reset additions: *, *::before, *::after box-sizing, img max-width 100%
2. Navbar scroll effect: .navbar-scrolled class for bg-slate-950 + box-shadow
3. Hero decorative background: animated grid pattern using ::before pseudo-element with SVG grid
4. Floating orb animations: .glow-orb class with radial gradient + blur + float keyframe
5. Scroll animation system: [data-animate="fade-up"] starts opacity:0 translateY(30px),
   .is-visible transitions to opacity:1 translateY(0) with 0.6s ease
6. FAQ accordion: .faq-answer transition for height 0 → auto + smooth reveal
7. Card hover effects: subtle translateY(-4px) + border-color change + box-shadow glow
8. Custom scrollbar: thin, colored with accent
9. Blog post typography: .prose class for article content (headings, paragraphs, links)
10. Loading shimmer: @keyframes shimmer for skeleton loading states
11. Button press effect: active:scale-95 on .btn-primary
12. Stats number animation: .stat-number with counter animation class
13. Testimonial card: quote mark pseudo-element in large accent color
14. Mobile menu slide animation: transition for the mobile menu panel

Write production-quality CSS. Under 200 lines total."""

    return await _stream_file(
        system=_CSS_SYSTEM,
        user=user,
        max_tokens=3000,
        label="styles.css",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — scripts.js
# ─────────────────────────────────────────────────────────────────────────────

_JS_SYSTEM = """\
You are a senior JavaScript engineer. Output ONLY raw JavaScript — no markdown, no fences, no explanations.
Vanilla ES6+. No libraries. No console.log in production code.\
"""


async def _gen_scripts(plan: SitePlan) -> str:
    user = f"""Generate scripts.js for the {plan.brand} site.

REQUIRED FEATURES (implement ALL):

1. NAVBAR SCROLL EFFECT
   - On scroll, add class 'navbar-scrolled' + 'bg-slate-950/90' + 'backdrop-blur-xl' + 'shadow-xl shadow-black/20' to #navbar
   - Remove when scrolled back to top

2. MOBILE MENU TOGGLE
   - #mobile-menu-btn click toggles #mobile-menu hidden/visible
   - Toggle #menu-icon-open and #menu-icon-close visibility
   - Close menu when clicking outside or on a link

3. SCROLL ANIMATIONS (IntersectionObserver)
   - Observe all [data-animate] elements
   - Add class 'is-visible' when 20% visible
   - Support staggered delays: add style.transitionDelay based on nth-child index

4. FAQ ACCORDION
   - .faq-item click toggles .faq-answer visibility
   - Animate height from 0 to scrollHeight with CSS transition
   - Toggle + → × icon on the trigger button
   - Only one FAQ open at a time

5. STATS COUNTER ANIMATION
   - When .stat-number enters viewport, animate from 0 to its data-target value
   - Support suffix (K, %, +, /5) from data-suffix attribute
   - Duration: 1500ms ease-out

6. SMOOTH SCROLL
   - All <a href="#..."> links scroll smoothly
   - Offset by navbar height (80px)

7. CONTACT FORM HANDLER (id="contact-form")
   - Prevent default submit
   - Validate required fields (name, email, message)
   - Show loading state on button
   - After 1200ms delay, show success message div (id="form-success")
   - Hide form, show success with slide-in animation
   - Success message: professional confirmation text in {plan.lang}

8. NEWSLETTER FORM HANDLER (id="newsletter-form")
   - Same pattern: validate email → loading → success inline message

9. ACTIVE NAV LINK
   - Highlight current page nav link based on window.location.pathname

Keep code clean. No jQuery. Under 180 lines."""

    return await _stream_file(
        system=_JS_SYSTEM,
        user=user,
        max_tokens=3500,
        label="scripts.js",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Blog Post pages
# ─────────────────────────────────────────────────────────────────────────────

_POST_SYSTEM = """\
You are a senior content writer and front-end developer specializing in SEO-optimized long-form articles.
Output ONLY raw HTML — no markdown fences, no explanations.
Start with <!DOCTYPE html> and end with </html>.

ARTICLE REQUIREMENTS:
- Minimum 900 words of actual article copy (not counting HTML tags)
- Proper semantic structure: <article>, <header>, <section>, <aside>
- All headings properly nested: one <h1> = article title, multiple <h2>, <h3> underneath
- Include a "Table of Contents" sidebar or top section with anchor links to h2 sections
- Featured image at top with proper alt text
- Author byline section (use realistic author name and Unsplash avatar)
- Estimated reading time calculation
- "Related articles" section at the bottom linking to other posts
- Social share buttons (decorative, with proper aria labels)
- Progress bar at top of page showing scroll progress\
"""


async def _gen_blog_post(plan: SitePlan, idx: int) -> str:
    if idx >= len(plan.blog_posts):
        return _fallback_post(plan, idx)

    post = plan.blog_posts[idx]
    a = _accent_classes(plan)

    # Build other posts for "related" links
    other_posts = [p for i, p in enumerate(plan.blog_posts) if i != idx]
    related_json = json.dumps(
        [{"title": p.title, "filename": p.filename} for p in other_posts],
        ensure_ascii=False
    )

    head = _shared_head(
        plan,
        f"{post.title} | {plan.brand}",
        post.meta_desc,
    )
    navbar = _shared_navbar(plan, "blog")
    footer = _shared_footer(plan)
    # Build section outline (compact — generator writes ALL content)
    outline_lines = []
    for i, h2 in enumerate(post.section_headings):
        outline_lines.append(f"  H2: {h2}")
        h3s = post.h3_per_section[i] if i < len(post.h3_per_section) else []
        for h3 in h3s:
            outline_lines.append(f"    H3: {h3}")
    outline = "\n".join(outline_lines)

    # JSON-LD for Article
    jsonld = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{post.title}",
  "description": "{post.meta_desc}",
  "image": "https://images.unsplash.com/photo-{post.hero_unsplash_id}?auto=format&fit=crop&q=80&w=1200",
  "author": {{"@type": "Person", "name": "Equipo {plan.brand}"}},
  "publisher": {{"@type": "Organization", "name": "{plan.brand}"}},
  "datePublished": "{datetime.now().strftime('%Y-%m-%d')}",
  "dateModified": "{datetime.now().strftime('%Y-%m-%d')}",
  "mainEntityOfPage": {{"@type": "WebPage", "@id": "{post.filename}"}}
}}
</script>"""

    user = f"""Build the complete {post.filename} blog article page.

Brand: {plan.brand}
Language: {plan.lang}
Accent: {a["name"]}

ARTICLE:
  Title (H1): "{post.title}"
  Meta desc: "{post.meta_desc}"
  Hero image: https://images.unsplash.com/photo-{post.hero_unsplash_id}?auto=format&fit=crop&q=80&w=1200&h=630

OUTLINE — YOU write ALL full content based on these headings:
{outline}

RELATED ARTICLES (for sidebar + bottom section):
{related_json}

CONTENT RULES:
- Write ALL paragraphs from scratch (do NOT leave any section thin)
- Each H2 section: 2-3 full paragraphs, 100-150 words each
- Each H3: 1-2 paragraphs, 80-100 words each
- TOTAL article text MUST exceed 900 words
- ALL text in language: {plan.lang}
- Table of Contents: anchor links to each H2 (ids like "section-1", "section-2"…)
- Author: realistic Spanish/Latin name + role + avatar photo above

LAYOUT:
- Two-column desktop: <main class="lg:grid lg:grid-cols-3 lg:gap-8">
  - Article: <article class="lg:col-span-2 prose"> with full content
  - Sidebar: <aside class="lg:col-span-1 space-y-6"> with TOC + related + CTA
- Mobile: single column
- Reading progress bar: <div id="reading-progress"> fixed at top, accent color

ADD this JSON-LD before </head>: {jsonld}

EXACT HEAD (copy verbatim, insert JSON-LD before </head>): {head}
EXACT NAVBAR (copy verbatim): {navbar}
EXACT FOOTER (copy verbatim): {footer}

Generate the COMPLETE article page — full written content, no placeholders."""

    html = await _stream_file(
        system=_POST_SYSTEM,
        user=user,
        max_tokens=8192,
        label=post.filename,
    )
    return _ensure_minimum_html(html, plan, post.filename)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — blog.html (grid index)
# ─────────────────────────────────────────────────────────────────────────────

async def _gen_blog_index(plan: SitePlan) -> str:
    a = _accent_classes(plan)
    head = _shared_head(
        plan,
        f"Blog | {plan.brand}",
        f"Artículos y guías sobre {plan.keyword}. Recursos expertos para {plan.brand}.",
    )
    navbar = _shared_navbar(plan, "blog")
    footer = _shared_footer(plan)
    posts_json = json.dumps(
        [
            {
                "title": p.title, "filename": p.filename,
                "meta_desc": p.meta_desc, "hero_unsplash_id": p.hero_unsplash_id,
                "read_time": "8 min",
            }
            for p in plan.blog_posts
        ],
        ensure_ascii=False, indent=2
    )

    jsonld = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Blog",
  "name": "Blog de {plan.brand}",
  "description": "Artículos sobre {plan.keyword}",
  "url": "blog.html"
}}
</script>"""

    user = f"""Build the complete blog.html page for {plan.brand}.
Brand: {plan.brand} | Language: {plan.lang} | Accent: {a["name"]}

POSTS TO DISPLAY:
{posts_json}

PAGE STRUCTURE:
1. USE EXACT HEAD BLOCK: {head}
   ADD this before </head>: {jsonld}
2. USE EXACT NAVBAR (copy verbatim): {navbar}
3. HERO SECTION:
   - Page title "Blog" in large font-serif, subtitle about the niche
   - Breadcrumb: Inicio > Blog
   - Category filter pills (decorative): All, Guías, Tutoriales, Estrategias
4. FEATURED POST (first post in full-width card):
   - Large hero image (w=1200&h=630), title, excerpt, read time, CTA button
   - Accent border-left highlight
5. POSTS GRID (remaining posts in 2-3 column grid):
   - Each card: image (w=600&h=400), category badge, title (font-serif), excerpt, author avatar + name + date, read time
   - Cards use bg-slate-900 border-slate-700/50 rounded-2xl hover effect
6. NEWSLETTER CTA SECTION:
   - Highlighted section with email input + subscribe button (id="newsletter-form")
   - "{plan.brand} Weekly" framing
7. USE EXACT FOOTER (copy verbatim): {footer}

Generate the COMPLETE blog.html. All 3 posts must appear. Full professional design."""

    html = await _stream_file(
        system=_HTML_SYSTEM,
        user=user,
        max_tokens=6000,
        label="blog.html",
    )
    return _ensure_minimum_html(html, plan, "blog.html")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — contact.html
# ─────────────────────────────────────────────────────────────────────────────

async def _gen_contact(plan: SitePlan) -> str:
    a = _accent_classes(plan)
    head = _shared_head(
        plan,
        f"Contacto | {plan.brand}",
        f"Contacta con {plan.brand}. Estamos aquí para ayudarte con todo lo relacionado con {plan.keyword}.",
    )
    navbar = _shared_navbar(plan, "contact")
    footer = _shared_footer(plan)

    jsonld = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "ContactPage",
  "name": "Contacto — {plan.brand}",
  "description": "Página de contacto de {plan.brand}",
  "url": "contact.html"
}}
</script>"""

    user = f"""Build the complete contact.html page for {plan.brand}.
Brand: {plan.brand} | Language: {plan.lang} | Accent: {a["name"]}
Contact email: {plan.contact_email}

PAGE STRUCTURE:
1. USE EXACT HEAD BLOCK: {head}
   ADD this before </head>: {jsonld}
2. USE EXACT NAVBAR (copy verbatim): {navbar}
3. HERO SECTION (compact, no full-viewport):
   - H1: "Hablemos" or equivalent in {plan.lang}
   - Subtitle: Encouraging contact text related to {plan.keyword}
   - Breadcrumb: Inicio > Contacto
4. TWO-COLUMN LAYOUT:
   LEFT COLUMN — Contact Form (id="contact-form"):
   - Full Name (required), Email (required), Phone (optional),
     Subject (select with 4-5 relevant options), Message textarea (required)
   - Submit button with loading state text
   - Success message div (id="form-success") initially hidden:
     Professional confirmation with ✓ icon
   - All labels in {plan.lang}

   RIGHT COLUMN — Contact Info:
   - Email card: icon + {plan.contact_email}
   - Response time card: "Respondemos en menos de 24h"
   - Location card: "Disponible online, en todo el mundo"
   - Hours card: "Lunes a Viernes, 9:00 - 18:00"
   - Trust badges: 3 small cards with icons (🔒 Datos seguros, ⚡ Respuesta rápida, ✓ Sin compromiso)

5. FAQ MINI-SECTION (3 quick questions about contacting):
   - Why contact us?, What happens after I send?, Response time?

6. USE EXACT FOOTER (copy verbatim): {footer}

Generate the COMPLETE contact.html. Professional, trustworthy design."""

    html = await _stream_file(
        system=_HTML_SYSTEM,
        user=user,
        max_tokens=6000,
        label="contact.html",
    )
    return _ensure_minimum_html(html, plan, "contact.html")


# ─────────────────────────────────────────────────────────────────────────────
# Guard / fallback helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_tailwind(html: str) -> str:
    if "cdn.tailwindcss.com" not in html:
        html = html.replace(
            "</head>",
            '<script src="https://cdn.tailwindcss.com"></script>\n</head>',
            1,
        )
    return html


def _ensure_minimum_html(html: str, plan: SitePlan, label: str) -> str:
    if not html.strip().startswith("<!DOCTYPE") and "<html" not in html:
        logger.warning(f"[AssetFactory] {label} missing DOCTYPE — prepending")
        html = "<!DOCTYPE html>\n<html lang='es'>\n<head></head>\n<body>\n" + html + "\n</body>\n</html>"
    html = _ensure_tailwind(html)
    # Ensure scripts.js is linked
    if "scripts.js" not in html:
        html = html.replace("</body>", '<script src="scripts.js"></script>\n</body>', 1)
    # Ensure styles.css is linked
    if "styles.css" not in html:
        html = html.replace("</head>", '<link rel="stylesheet" href="styles.css">\n</head>', 1)
    return html


def _fallback_post(plan: SitePlan, idx: int) -> str:
    return f"""<!DOCTYPE html>
<html lang="{plan.lang}">
<head>
  <meta charset="UTF-8">
  <title>Artículo {idx + 1} | {plan.brand}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="styles.css">
</head>
<body class="bg-slate-950 text-white">
  <div class="max-w-3xl mx-auto px-4 py-20 text-center">
    <h1 class="text-3xl font-bold mb-4">Artículo en preparación</h1>
    <p class="text-slate-400">Vuelve pronto para leer este artículo sobre {plan.keyword}.</p>
    <a href="index.html" class="mt-8 inline-block bg-emerald-500 text-slate-950 px-6 py-3 rounded-xl font-semibold">Volver al inicio</a>
  </div>
  <script src="scripts.js"></script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Public: generate_asset — orchestrates all phases
# ─────────────────────────────────────────────────────────────────────────────

async def generate_asset(
    keyword: str,
    asset_type: AssetType,
    monetization: MonetizationModel,
) -> dict[str, str]:
    """
    Full multi-page generation pipeline.
    Returns dict[filename → content] for 8 files.

    When SIMULATE_AI=True, generates realistic mock sites instantly
    without calling the Anthropic API (investor demo mode).
    """
    if settings.SIMULATE_AI:
        logger.info(f"[AssetFactory] 🎭 SIMULATE_AI mode — generating mock site for '{keyword}'")
        return _generate_mock_site(keyword, asset_type, monetization)

    logger.info(f"[AssetFactory] ▶ Starting enterprise generation: '{keyword}'")

    # Phase 0: Site plan (sequential — all other phases depend on this)
    plan = await _generate_site_plan(keyword, asset_type, monetization)

    # Phase 1: Core files (parallel)
    logger.info("[AssetFactory] Phase 1: Core files (index + styles + scripts)")
    index_html, styles_css, scripts_js = await asyncio.gather(
        _gen_index(plan),
        _gen_styles(plan),
        _gen_scripts(plan),
    )

    # Phase 2: Blog posts (parallel — most token-intensive phase)
    logger.info("[AssetFactory] Phase 2: Blog posts (3 articles in parallel)")
    post1, post2, post3 = await asyncio.gather(
        _gen_blog_post(plan, 0),
        _gen_blog_post(plan, 1),
        _gen_blog_post(plan, 2),
    )

    # Phase 3: Blog index + Contact (parallel)
    logger.info("[AssetFactory] Phase 3: Blog index + Contact page")
    blog_html, contact_html = await asyncio.gather(
        _gen_blog_index(plan),
        _gen_contact(plan),
    )

    files = {
        "index.html":   index_html,
        "blog.html":    blog_html,
        "post-1.html":  post1,
        "post-2.html":  post2,
        "post-3.html":  post3,
        "contact.html": contact_html,
        "styles.css":   styles_css,
        "scripts.js":   scripts_js,
    }

    total_chars = sum(len(v) for v in files.values())
    logger.info(
        f"[AssetFactory] ✅ Complete — {len(files)} files, "
        f"{total_chars:,} chars total | "
        f"HTML: {len(index_html):,} | CSS: {len(styles_css):,} | JS: {len(scripts_js):,}"
    )
    return files


# ─────────────────────────────────────────────────────────────────────────────
# Mock Site Generator — SIMULATE_AI mode (no Anthropic API calls)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_mock_site(
    keyword: str,
    asset_type: AssetType,
    monetization: MonetizationModel,
) -> dict[str, str]:
    """Generate a high-quality mock website instantly for investor demos."""
    from textwrap import dedent
    import random

    title = keyword.replace("-", " ").title()
    slug = re.sub(r"[^a-z0-9-]", "-", keyword.lower().strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    accent = random.choice(["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899"])
    year = datetime.utcnow().year

    kw_short = keyword[:25]
    _render = lambda name, **kw: _MOCK_TEMPLATES[name].format(
        title=title, slug=slug, keyword=keyword, keyword_short=kw_short,
        accent=accent, year=year,
        monetization=monetization.value, asset_type=asset_type.value, **kw
    )

    return {
        "index.html":   _render("index"),
        "blog.html":    _render("blog"),
        "post-1.html":  _render("post", num="1", post_title=f"Guía Completa de {title} en {year}"),
        "post-2.html":  _render("post", num="2", post_title=f"Top 5 {title} — Comparativa y Precios"),
        "post-3.html":  _render("post", num="3", post_title=f"¿Vale la Pena Invertir en {title}?"),
        "contact.html": _render("contact"),
        "styles.css":   _MOCK_CSS.format(accent=accent),
        "scripts.js":   _MOCK_JS,
    }

_MOCK_CSS = """/* Auto-generated by AROS — Autonomous Revenue OS */
:root {{ --accent: {accent}; --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --muted: #64748b; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height:1.6; }}
header {{ background: linear-gradient(135deg, var(--accent), #1e293b); padding: 5rem 2rem; text-align: center; }}
header h1 {{ font-size: 2.8rem; font-weight:800; margin-bottom:1rem; letter-spacing:-0.02em; }}
header p {{ font-size:1.2rem; opacity:0.85; max-width:600px; margin:0 auto; }}
.cta {{ display:inline-block; margin-top:1.5rem; background:white; color:var(--accent); padding:0.8rem 2rem; border-radius:50px; font-weight:700; text-decoration:none; transition:transform .2s; }}
.cta:hover {{ transform:scale(1.05); }}
.container {{ max-width:1100px; margin:0 auto; padding:3rem 1.5rem; }}
section {{ margin:3rem 0; }}
section h2 {{ font-size:1.8rem; margin-bottom:1.5rem; color:var(--accent); }}
.grid {{ display:grid; gap:1.5rem; }}
.grid-2 {{ grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); }}
.grid-3 {{ grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); }}
.grid-4 {{ grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); }}
.card {{ background:var(--card); border-radius:16px; padding:2rem; border:1px solid rgba(255,255,255,0.05); transition:transform .2s,box-shadow .2s; }}
.card:hover {{ transform:translateY(-4px); box-shadow:0 12px 40px rgba(0,0,0,0.3); }}
.card h3 {{ color:var(--accent); margin-bottom:0.5rem; }}
.card p {{ color:var(--muted); font-size:0.95rem; }}
.stats {{ display:flex; gap:2rem; flex-wrap:wrap; justify-content:center; margin:2rem 0; }}
.stat {{ text-align:center; }}
.stat-num {{ font-size:2.5rem; font-weight:800; color:var(--accent); }}
.stat-label {{ font-size:0.85rem; color:var(--muted); }}
footer {{ background:var(--card); text-align:center; padding:2rem; color:var(--muted); font-size:0.9rem; margin-top:3rem; border-top:1px solid rgba(255,255,255,0.05); }}
.testimonial {{ background:var(--card); border-radius:16px; padding:2rem; border-left:4px solid var(--accent); margin:1rem 0; }}
.testimonial .quote {{ font-style:italic; margin-bottom:1rem; }}
.testimonial .author {{ font-weight:600; color:var(--accent); }}
.faq-item {{ margin-bottom:1.5rem; padding-bottom:1.5rem; border-bottom:1px solid rgba(255,255,255,0.05); }}
.faq-item h3 {{ margin-bottom:0.5rem; }}
.badge {{ display:inline-block; background:var(--accent); color:white; padding:0.25rem 0.75rem; border-radius:50px; font-size:0.75rem; font-weight:600; }}
.price {{ font-size:2rem; font-weight:800; color:var(--accent); }}
nav {{ display:flex; justify-content:space-between; align-items:center; padding:1rem 2rem; background:rgba(15,23,42,0.95); position:sticky; top:0; z-index:100; backdrop-filter:blur(10px); border-bottom:1px solid rgba(255,255,255,0.05); }}
nav .logo {{ font-weight:800; font-size:1.2rem; color:var(--accent); }}
nav .links {{ display:flex; gap:1.5rem; }}
nav .links a {{ color:var(--muted); text-decoration:none; font-size:0.9rem; transition:color .2s; }}
nav .links a:hover {{ color:var(--accent); }}
.blog-post {{ max-width:800px; margin:0 auto; }}
.blog-post h2 {{ margin-bottom:1rem; }}
.blog-post .meta {{ color:var(--muted); font-size:0.9rem; margin-bottom:2rem; }}
.blog-post p {{ margin-bottom:1.2rem; color:#cbd5e1; line-height:1.8; }}
.blog-post h2 {{ margin-top:2.5rem; }}
table {{ width:100%; border-collapse:collapse; margin:2rem 0; }}
th, td {{ padding:0.75rem 1rem; text-align:left; border-bottom:1px solid rgba(255,255,255,0.05); }}
th {{ color:var(--accent); font-weight:600; }}
.progress-bar {{ height:4px; background:rgba(255,255,255,0.1); position:fixed; top:0; left:0; z-index:200; transition:width .3s; }}
.progress-bar::after {{ content:''; display:block; height:100%; background:var(--accent); width:var(--progress,0%); }}
@media (max-width:768px) {{ header h1 {{ font-size:2rem; }} header {{ padding:4rem 1.5rem; }} nav .links {{ display:none; }} }}
"""

_MOCK_JS = """// AROS Traffic Tracking — Autonomous Revenue OS
(function(){{var b=document.querySelector('meta[name="aros-asset-id"]');if(!b)return;var a=b.getAttribute('content');if(!a)return;var c='{AROS_API_URL}',d=performance.now(),e=function(){{var r=new XMLHttpRequest();r.open('POST',c+'/api/analytics/'+a+'/track',!0);r.setRequestHeader('Content-Type','application/json');r.send(JSON.stringify({{visits:1,conversions:0,revenue:0,ttfb:performance.now()-d}}))}};'requestIdleCallback'in window?requestIdleCallback(e):setTimeout(e,1000)}})();
document.addEventListener('DOMContentLoaded',function(){{document.querySelectorAll('a[href^="#"]').forEach(function(e){{e.addEventListener('click',function(t){{t.preventDefault();var d=document.querySelector(this.getAttribute('href'));d&&d.scrollIntoView({{behavior:'smooth'}})}})}});var a=document.querySelectorAll('.faq-item h3');a.forEach(function(e){{e.style.cursor='pointer';e.nextElementSibling&&(e.nextElementSibling.style.display='none');e.addEventListener('click',function(){{var n=this.nextElementSibling;n&&(n.style.display=n.style.display==='none'?'block':'none')}})}});window.addEventListener('scroll',function(){{var p=document.querySelector('.progress-bar');if(!p)return;var s=document.documentElement.scrollTop,dh=document.documentElement.scrollHeight- window.innerHeight;p.style.setProperty('--progress',Math.min((s/dh)*100,100)+'%')}});var b=document.querySelectorAll('.stat-num[data-count]');b.forEach(function(e){{var t=parseInt(e.getAttribute('data-count')),d=2000,i=t/d*10,s=setInterval(function(){{var c=parseInt(e.textContent.replace(/[^0-9]/g,''))||0;c+=Math.ceil(i);c>=t&&(c=t,clearInterval(s));e.textContent=c.toLocaleString()+'%'}},10)}})}});
(function(){{var s=document.createElement('script');s.src='https://cdn.tailwindcss.com';document.head.appendChild(s)}})();
"""

_MOCK_TEMPLATES = {
    "index": """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="aros-asset-id" content="__ASSET_ID__">
<title>{title} — La Mejor Opción en {year}</title>
<meta name="description" content="Descubre {title}. Guía completa, precios, comparativas y opiniones actualizadas. ¡Entra ahora!">
<meta property="og:title" content="{title}">
<meta property="og:description" content="La guía definitiva de {title} en {year}">
<meta property="og:type" content="website">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"{title}","description":"Guía completa de {title}"}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,700;1,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="progress-bar"></div>
<nav>
  <div class="logo">⚡ {keyword_short}</div>
  <div class="links">
    <a href="index.html">Inicio</a>
    <a href="blog.html">Blog</a>
    <a href="contact.html">Contacto</a>
  </div>
</nav>

<header>
  <h1>{title}: La Guía Definitiva</h1>
  <p>Todo lo que necesitas saber sobre {keyword}. Análisis, comparativas y las mejores recomendaciones actualizadas en {year}.</p>
  <a href="#reviews" class="cta">Ver Recomendaciones →</a>
</header>

<div class="container">
  <section id="stats">
    <div class="stats">
      <div class="stat"><div class="stat-num"><span data-count="98">0</span></div><div class="stat-label">Clientes Satisfechos</div></div>
      <div class="stat"><div class="stat-num"><span data-count="2500">0</span>+</div><div class="stat-label">Productos Analizados</div></div>
      <div class="stat"><div class="stat-num"><span data-count="15">0</span>K</div><div class="stat-label">Lectores Mensuales</div></div>
      <div class="stat"><div class="stat-num"><span data-count="4">0</span>.8</div><div class="stat-label">Valoración Media</div></div>
    </div>
  </section>

  <section id="features">
    <h2>¿Por Qué Elegir {title}?</h2>
    <div class="grid grid-3">
      <div class="card"><h3>🔍 Análisis Exhaustivo</h3><p>Hemos probado y comparado decenas de opciones para traerte solo lo mejor en {keyword}.</p></div>
      <div class="card"><h3>💰 Mejor Precio Garantizado</h3><p>Trabajamos con los principales proveedores para asegurarte el mejor precio del mercado.</p></div>
      <div class="card"><h3>⭐ Opiniones Reales</h3><p>Miles de usuarios avalan nuestras recomendaciones. Lee sus experiencias reales.</p></div>
      <div class="card"><h3>🚀 Envío Rápido</h3><p>Recibe tu pedido en 24-48h. Devoluciones gratuitas durante 30 días.</p></div>
      <div class="card"><h3>🛡️ Garantía Extendida</h3><p>Todos los productos recomendados incluyen garantía mínima de 2 años.</p></div>
      <div class="card"><h3>📞 Soporte 24/7</h3><p>Nuestro equipo de expertos está disponible para resolver cualquier duda.</p></div>
    </div>
  </section>

  <section id="reviews">
    <h2>Nuestras Recomendaciones Top</h2>
    <div class="grid grid-2">
      <div class="card"><span class="badge">TOP 1</span><h3 style="margin-top:0.5rem">{title} Premium</h3><p>La opción más completa del mercado. Rendimiento superior, materiales de primera calidad y diseño innovador.</p><div class="price">€299</div></div>
      <div class="card"><h3>{title} Standard</h3><p>Excelente relación calidad-precio. Perfecta para quienes buscan lo mejor sin gastar de más.</p><div class="price">€149</div></div>
    </div>
  </section>

  <section id="testimonials">
    <h2>Lo Que Dicen Nuestros Clientes</h2>
    <div class="testimonial"><p class="quote">"Increíble. Llevaba meses buscando {keyword} y aquí encontré justo lo que necesitaba. Recomendado 100%."</p><p class="author">— María G., Madrid</p></div>
    <div class="testimonial"><p class="quote">"La guía más completa que he leído. Me ayudó a decidir en minutos lo que no conseguí en semanas de búsqueda."</p><p class="author">— Carlos R., Barcelona</p></div>
    <div class="testimonial"><p class="quote">"Pensé que era demasiado bueno para ser verdad. Pero los resultados hablan por sí solos. Volveré a comprar."</p><p class="author">— Ana L., Valencia</p></div>
  </section>

  <section id="faq">
    <h2>Preguntas Frecuentes</h2>
    <div class="faq-item"><h3>¿Es fiable comprar {keyword} online?</h3><p>Absolutamente. Trabajamos solo con vendedores verificados que ofrecen garantía y devolución.</p></div>
    <div class="faq-item"><h3>¿Cuánto tarda el envío?</h3><p>El envío estándar es de 2-3 días laborables. También ofrecemos envío express 24h.</p></div>
    <div class="faq-item"><h3>¿Qué garantía tienen los productos?</h3><p>Todos los productos incluyen al menos 2 años de garantía del fabricante.</p></div>
    <div class="faq-item"><h3>¿Puedo devolver el producto si no me convence?</h3><p>Sí, dispones de 30 días para devoluciones gratuitas sin preguntas.</p></div>
  </section>
</div>

<footer>
  <p>© {year} {keyword} — Todos los derechos reservados</p>
  <p style="margin-top:0.5rem;font-size:0.8rem">Generado por AROS · Autonomous Revenue Operating System</p>
</footer>
<script src="scripts.js"></script>
</body>
</html>""",

    "blog": """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="aros-asset-id" content="__ASSET_ID__">
<title>Blog — {title}</title>
<meta name="description" content="Artículos, guías y consejos sobre {keyword}. Mantente al día con las últimas novedades.">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Blog","name":"Blog de {title}"}}</script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,700;1,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<nav><div class="logo">⚡ {keyword_short}</div><div class="links"><a href="index.html">Inicio</a><a href="blog.html">Blog</a><a href="contact.html">Contacto</a></div></nav>
<header><h1>Blog de {title}</h1><p>Guías, comparativas y consejos de expertos</p></header>
<div class="container">
  <div class="grid grid-2">
    <article class="card"><span class="badge">GUÍA</span><h3 style="margin-top:0.5rem"><a href="post-1.html" style="color:inherit;text-decoration:none">Guía Completa de {title} en {year}</a></h3><p>Todo lo que necesitas saber para tomar la mejor decisión de compra. Análisis detallado.</p></article>
    <article class="card"><span class="badge">COMPARATIVA</span><h3 style="margin-top:0.5rem"><a href="post-2.html" style="color:inherit;text-decoration:none">Top 5 {title} — Comparativa y Precios</a></h3><p>Comparamos los 5 mejores productos del mercado para que elijas con criterio.</p></article>
    <article class="card"><span class="badge">ANÁLISIS</span><h3 style="margin-top:0.5rem"><a href="post-3.html" style="color:inherit;text-decoration:none">¿Vale la Pena Invertir en {title}?</a></h3><p>Analizamos el retorno de inversión, calidad y durabilidad de las mejores opciones.</p></article>
  </div>
</div>
<footer><p>© {year} {keyword} · Powered by AROS</p></footer>
<script src="scripts.js"></script>
</body>
</html>""",

    "post": """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="aros-asset-id" content="__ASSET_ID__">
<title>{post_title} — {title}</title>
<meta name="description" content="{post_title}. Artículo detallado con análisis, datos, y recomendaciones de expertos.">
<meta property="og:title" content="{post_title}">
<meta property="og:type" content="article">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"{post_title}","author":{{"@type":"Organization","name":"{title}"}},"datePublished":"{year}-01-15"}}</script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,700;1,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="progress-bar"></div>
<nav><div class="logo">⚡ {keyword_short}</div><div class="links"><a href="index.html">Inicio</a><a href="blog.html">Blog</a><a href="contact.html">Contacto</a></div></nav>
<div class="container">
  <article class="blog-post">
    <span class="badge">ARTÍCULO</span>
    <h1 style="font-size:2rem;margin-top:0.75rem">{post_title}</h1>
    <p class="meta">Publicado el 15 de enero de {year} · 8 min de lectura</p>
    <h2>Introducción</h2>
    <p>El mercado de {keyword} ha experimentado un crecimiento sin precedentes en los últimos años. Cada vez más consumidores buscan información fiable antes de tomar una decisión de compra, y es precisamente ahí donde entra en juego esta guía.</p>
    <p>En este artículo, analizaremos en profundidad todos los aspectos relevantes de {keyword}, desde las características técnicas hasta la relación calidad-precio, pasando por las opiniones de usuarios reales y las tendencias del mercado.</p>
    <h2>¿Qué Hace Especial a {title}?</h2>
    <p>Hay varios factores que diferencian a {keyword} de otras alternativas en el mercado. En primer lugar, la calidad de los materiales utilizados garantiza una durabilidad superior. En segundo lugar, la atención al cliente es ampliamente reconocida como una de las mejores del sector.</p>
    <p>Además, los precios son altamente competitivos, especialmente si se comparan con productos de gamas similares. Esto convierte a {keyword} en una opción muy atractiva para el consumidor medio.</p>
    <h2>Comparativa de Características</h2>
    <table><thead><tr><th>Característica</th><th>{title} Premium</th><th>{title} Standard</th><th>Competidor</th></tr></thead><tbody><tr><td>Calidad</td><td>⭐⭐⭐⭐⭐</td><td>⭐⭐⭐⭐</td><td>⭐⭐⭐</td></tr><tr><td>Precio</td><td>€299</td><td>€149</td><td>€199</td></tr><tr><td>Garantía</td><td>3 años</td><td>2 años</td><td>1 año</td></tr><tr><td>Envío</td><td>24h</td><td>48h</td><td>3-5 días</td></tr></tbody></table>
    <h2>Conclusión</h2>
    <p>Después de analizar exhaustivamente todas las opciones disponibles en el mercado de {keyword}, podemos afirmar con seguridad que {title} representa la mejor relación calidad-precio del momento actual.</p>
    <p>Si estás buscando {keyword}, nuestra recomendación es clara: invierte en calidad y no te arrepentirás. La diferencia de precio se amortiza rápidamente con la durabilidad y el rendimiento superiores.</p>
    <a href="index.html" class="cta">← Volver al Inicio</a>
  </article>
</div>
<footer><p>© {year} {keyword} · Powered by AROS</p></footer>
<script src="scripts.js"></script>
</body>
</html>""",

    "contact": """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="aros-asset-id" content="__ASSET_ID__">
<title>Contacto — {title}</title>
<meta name="description" content="Contacta con el equipo de {title}. Estamos aquí para ayudarte.">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"ContactPage","name":"Contacto de {title}"}}</script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,700;1,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<nav><div class="logo">⚡ {keyword_short}</div><div class="links"><a href="index.html">Inicio</a><a href="blog.html">Blog</a><a href="contact.html">Contacto</a></div></nav>
<header><h1>Contacto</h1><p>Estamos aquí para ayudarte. Escríbenos y te responderemos en menos de 24h.</p></header>
<div class="container" style="max-width:600px">
  <div class="grid grid-2" style="margin-bottom:2rem">
    <div class="card"><h3>📧 Email</h3><p style="color:var(--accent)">hola@{slug}.com</p></div>
    <div class="card"><h3>📞 Teléfono</h3><p style="color:var(--accent)">+34 900 123 456</p></div>
  </div>
  <div class="card">
    <h3>Envíanos un mensaje</h3>
    <div class="grid" style="gap:1rem;margin-top:1rem">
      <input type="text" placeholder="Tu nombre" style="background:var(--bg);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:0.75rem;color:white;width:100%">
      <input type="email" placeholder="Tu email" style="background:var(--bg);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:0.75rem;color:white;width:100%">
      <textarea placeholder="Tu mensaje" rows="4" style="background:var(--bg);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:0.75rem;color:white;width:100%;resize:vertical"></textarea>
      <button class="cta" style="border:none;cursor:pointer;font-size:1rem">Enviar Mensaje</button>
    </div>
  </div>
</div>
<footer><p>© {year} {keyword} · Powered by AROS</p></footer>
<script src="scripts.js"></script>
</body>
</html>"""
}


# ─────────────────────────────────────────────────────────────────────────────
# Public: generate_landing_page — generate + persist to DB
# ─────────────────────────────────────────────────────────────────────────────

async def generate_landing_page(
    keyword: str,
    db: AsyncSession,
    asset_type: AssetType = AssetType.LANDING_PAGE,
    monetization: MonetizationModel = MonetizationModel.AFFILIATES,
) -> Asset:
    """
    Status flow:  GENERATING  →  CREATED (success)
                             ↘  ERROR   (failure)
    """
    asset = Asset(
        keyword=keyword,
        type=asset_type,
        monetization_model=monetization,
        status=AssetStatus.GENERATING,
        cost=0.25,  # 9 API calls ≈ higher cost than v1
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    logger.info(f"[AssetFactory] Asset #{asset.id} created — generating '{keyword}'")

    try:
        files = await generate_asset(keyword, asset_type, monetization)
    except Exception as exc:
        asset.status = AssetStatus.ERROR
        asset.error_message = str(exc)[:500]
        asset.updated_at = datetime.utcnow()
        await db.commit()
        logger.error(f"[AssetFactory] Asset #{asset.id} → ERROR: {exc}")
        raise

    # Inject tracking pixel into every HTML file
    for fname in list(files.keys()):
        if fname.endswith(".html"):
            files[fname] = inject_tracking_pixel(files[fname], asset.id)

    asset.content_html = files["index.html"]
    asset.content_files = json.dumps(files, ensure_ascii=False)
    asset.status = AssetStatus.CREATED
    asset.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(asset)

    html_sizes = {k: len(v) for k, v in files.items() if k.endswith(".html")}
    logger.info(
        f"[AssetFactory] Asset #{asset.id} → CREATED | "
        f"Files: {list(files.keys())} | Sizes: {html_sizes}"
    )
    return asset
