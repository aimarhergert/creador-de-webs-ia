"""
AI Provider Abstraction Layer — multi-backend with automatic fallback.

Supports:
  - Anthropic Claude (primary, paid)
  - DeepSeek (secondary, cheaper)
  - Free fallback (local mock / HuggingFace inference)

Priority: Anthropic → DeepSeek → Free (mock)
When SIMULATE_AI=True, all calls go to mock regardless.

Usage:
    provider = get_provider()
    response = await provider.generate(prompt, system="...", max_tokens=2000)
"""

import asyncio
import json
import logging
import os
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    text: str
    provider: str  # "anthropic" | "deepseek" | "mock"
    model: str
    tokens_used: int
    cost_est: float


class AIProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> AIResponse:
        ...


# ─────────────────────────────────────────────────────────────────────────────
# Anthropic Provider
# ─────────────────────────────────────────────────────────────────────────────

class AnthropicProvider(AIProvider):
    def __init__(self):
        self.model = "claude-sonnet-4-20250514"
        self.available = bool(settings.ANTHROPIC_API_KEY)

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4000, temperature: float = 0.7) -> AIResponse:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            kwargs["system"] = system
        resp = await client.messages.create(**kwargs)
        text = resp.content[0].text if resp.content else ""
        return AIResponse(
            text=text,
            provider="anthropic",
            model=self.model,
            tokens_used=resp.usage.input_tokens + resp.usage.output_tokens,
            cost_est=(resp.usage.input_tokens * 3 / 1_000_000 + resp.usage.output_tokens * 15 / 1_000_000),
        )


# ─────────────────────────────────────────────────────────────────────────────
# DeepSeek Provider (OpenAI-compatible API)
# ─────────────────────────────────────────────────────────────────────────────

DEEPSEEK_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"


class DeepSeekProvider(AIProvider):
    def __init__(self):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.available = bool(self.api_key)

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4000, temperature: float = 0.7) -> AIResponse:
        import httpx
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"{DEEPSEEK_BASE}/chat/completions",
                headers=headers,
                json={
                    "model": DEEPSEEK_MODEL,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return AIResponse(
                text=text,
                provider="deepseek",
                model=DEEPSEEK_MODEL,
                tokens_used=usage.get("total_tokens", 0),
                cost_est=(usage.get("prompt_tokens", 0) * 0.14 / 1_000_000 +
                          usage.get("completion_tokens", 0) * 0.28 / 1_000_000),
            )


# ─────────────────────────────────────────────────────────────────────────────
# Free / Mock Provider — returns high-quality mock responses for demo mode
# ─────────────────────────────────────────────────────────────────────────────

MOCK_SITE_PLAN_JSON = """{
  "brand": "{brand}",
  "tagline": "{tagline}",
  "accent": "{accent}",
  "accent_hex": "{accent_hex}",
  "hero_headline": "{hero_headline}",
  "hero_subheadline": "{hero_subheadline}",
  "hero_cta_primary": "Ver Recomendaciones",
  "hero_cta_secondary": "Comparar Precios",
  "hero_unsplash_id": "photo-{unsplash}",
  "stats": [
    {{"value": "98%", "label": "Clientes Satisfechos"}},
    {{"value": "2.500+", "label": "Productos Analizados"}},
    {{"value": "15K", "label": "Lectores Mensuales"}},
    {{"value": "4.8", "label": "Valoración Media"}}
  ],
  "features": [
    {{"icon": "search", "title": "Análisis Exhaustivo", "desc": "Probamos y comparamos decenas de opciones para traerte lo mejor."}},
    {{"icon": "dollar", "title": "Mejor Precio Garantizado", "desc": "Trabajamos con proveedores líderes para asegurar el mejor precio."}},
    {{"icon": "star", "title": "Opiniones Reales", "desc": "Miles de usuarios avalan nuestras recomendaciones con experiencias verificadas."}},
    {{"icon": "truck", "title": "Envío Rápido", "desc": "Recibe tu pedido en 24-48h con devoluciones gratuitas."}},
    {{"icon": "shield", "title": "Garantía Extendida", "desc": "Todos los productos incluyen garantía mínima de 2 años."}},
    {{"icon": "headset", "title": "Soporte 24/7", "desc": "Nuestro equipo de expertos está disponible para resolver tus dudas."}}
  ],
  "testimonials": [
    {{"name": "María G.", "role": "Compradora Verificada", "company": "Madrid", "quote": "Increíble. Llevaba meses buscando {keyword} y aquí encontré justo lo que necesitaba. Recomendado 100%.", "unsplash_id": "photo-1"}},
    {{"name": "Carlos R.", "role": "Cliente Premium", "company": "Barcelona", "quote": "La guía más completa que he leído. Me ayudó a decidir en minutos.", "unsplash_id": "photo-2"}},
    {{"name": "Ana L.", "role": "Compradora Frecuente", "company": "Valencia", "quote": "Pensé que era demasiado bueno para ser verdad. Los resultados hablan por sí solos.", "unsplash_id": "photo-3"}}
  ],
  "faq": [
    {{"q": "¿Es fiable comprar {keyword} online?", "a": "Absolutamente. Solo trabajamos con vendedores verificados que ofrecen garantía de devolución."}},
    {{"q": "¿Cuánto tarda el envío?", "a": "El envío estándar es de 2-3 días. Ofrecemos envío express 24h."}},
    {{"q": "¿Qué garantía tienen los productos?", "a": "Todos los productos recomendados incluyen mínimo 2 años de garantía."}},
    {{"q": "¿Puedo devolver el producto si no me convence?", "a": "Sí, 30 días de devolución gratuita sin preguntas."}}
  ],
  "blog_posts": [
    {{"title": "Guía Completa de {title} en {year}", "slug": "guia-completa", "meta_desc": "Todo sobre {keyword}. Análisis detallado, precios y recomendaciones.", "hero_unsplash_id": "photo-10", "section_headings": ["Introducción", "¿Qué hace especial a {title}?", "Comparativa", "Conclusión"], "h3_per_section": [["Contexto"], ["Calidad", "Precio"], ["Tabla"], ["Recomendación"]]}},
    {{"title": "Top 5 {title} — Comparativa y Precios", "slug": "top-5-comparativa", "meta_desc": "Top 5 {keyword}. Comparamos los mejores.", "hero_unsplash_id": "photo-11", "section_headings": ["Ranking", "Análisis", "Conclusión"], "h3_per_section": [["#1"], ["Pros y contras"], ["Veredicto"]]}},
    {{"title": "¿Vale la Pena Invertir en {title}?", "slug": "vale-la-pena", "meta_desc": "Análisis ROI de {keyword}.", "hero_unsplash_id": "photo-12", "section_headings": ["Inversión", "Retorno", "Conclusión"], "h3_per_section": [["Costes"], ["Beneficios"], ["Decisión"]]}}
  ]
}"""

SECTORS = {
    "tech": {"accent": "#3b82f6", "brands": ["TechNova", "ByteWise", "CodePeak"], "taglines": ["Tecnología que transforma", "Innovación sin límites", "El futuro es ahora"]},
    "health": {"accent": "#10b981", "brands": ["VitalCare", "MediPure", "HealthFirst"], "taglines": ["Tu salud, nuestra prioridad", "Bienestar garantizado", "Vive mejor"]},
    "finance": {"accent": "#8b5cf6", "brands": ["FinWise", "CapitalIQ", "MoneyFlow"], "taglines": ["Tu dinero crece solo", "Inversiones inteligentes", "Libertad financiera"]},
    "ecommerce": {"accent": "#f59e0b", "brands": ["ShopPeak", "BuyGenius", "ClickMart"], "taglines": ["Las mejores ofertas", "Calidad al mejor precio", "Compra inteligente"]},
    "education": {"accent": "#06b6d4", "brands": ["LearnPro", "SkillForge", "EduGenius"], "taglines": ["Aprende sin límites", "Conocimiento que transforma", "Tu futuro empieza aquí"]},
    "travel": {"accent": "#ec4899", "brands": ["ViajaSmart", "TripGenius", "WorldWise"], "taglines": ["Descubre el mundo", "Viajes inolvidables", "Aventura garantizada"]},
    "realestate": {"accent": "#84cc16", "brands": ["HomeWise", "PropMatch", "NestFinder"], "taglines": ["Tu hogar ideal", "Inversión segura", "Vive donde sueñas"]},
    "default": {"accent": "#6366f1", "brands": ["GeniusPick", "BestChoice", "TopSelector"], "taglines": ["La mejor elección", "Calidad garantizada", "Expertos en lo que hacemos"]},
}


class FreeProvider(AIProvider):
    """Zero-cost provider — returns realistic mock AI responses for demos."""

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4000, temperature: float = 0.7) -> AIResponse:
        await asyncio.sleep(random.uniform(0.2, 0.8))

        # System prompt takes priority for routing
        if system:
            if "market_analysis" in system.lower():
                return self._mock_generic(prompt)
            if "site_plan" in system.lower() or "plan_json" in system.lower():
                return self._mock_site_plan(prompt)
            if "html" in system.lower():
                return self._mock_html(prompt)
            if "blog" in system.lower() or "article" in system.lower():
                return self._mock_blog_post(prompt)

        prompt_lower = prompt.lower()

        # Site plan generation — stricter match
        if "site plan" in prompt_lower and "json" in prompt_lower:
            return self._mock_site_plan(prompt)

        # HTML generation — check for code generation intent
        if "<!DOCTYPE html>" in prompt or "genera html" in prompt_lower or "crea una landing" in prompt_lower:
            return self._mock_html(prompt)

        # CSS — must be explicitly requesting CSS
        if prompt_lower.strip().startswith("css") or "hoja de estilos" in prompt_lower:
            return self._mock_css(prompt)

        # Blog post — explicit request
        if "artículo de blog" in prompt_lower or "escribe un artículo" in prompt_lower or "blog post" in prompt_lower:
            return self._mock_blog_post(prompt)

        # Generic — return structured JSON for analysis requests
        return self._mock_generic(prompt)

    def _mock_site_plan(self, prompt: str) -> AIResponse:
        import re
        keyword = "producto"
        match = re.search(r'keyword["\':]+\s*["\']([^"\']+)', prompt)
        if not match:
            match = re.search(r'para\s+["\']?([^"\'.,]+)', prompt)
        if match:
            keyword = match.group(1)
        title = keyword.replace("-", " ").title()

        # Detect sector from keyword
        sector = self._detect_sector(keyword)
        info = SECTORS.get(sector, SECTORS["default"])
        brand = random.choice(info["brands"])
        tagline = random.choice(info["taglines"])

        from datetime import datetime
        year = datetime.utcnow().year

        plan = MOCK_SITE_PLAN_JSON.format(
            brand=brand, tagline=tagline,
            accent=sector, accent_hex=info["accent"],
            hero_headline=f"{title}: La Guía Definitiva {year}",
            hero_subheadline=f"Todo lo que necesitas saber sobre {keyword}. Análisis, comparativas y las mejores recomendaciones.",
            unsplash=random.randint(100, 999),
            keyword=keyword, title=title, year=year,
        )
        # Fix JSON-LD braces (escaped for format)
        plan = plan.replace("{{", "{").replace("}}", "}")
        return AIResponse(text=plan, provider="mock", model="free-v3", tokens_used=800, cost_est=0.0)

    def _mock_html(self, prompt: str) -> AIResponse:
        # Extract keyword from prompt
        import re
        keyword = "producto recomendado"
        match = re.search(r'keyword["\':]+\s*["\']([^"\']+)', prompt)
        if match:
            keyword = match.group(1)
        title = keyword.replace("-", " ").title()
        sector = self._detect_sector(keyword)

        from datetime import datetime
        year = datetime.utcnow().year
        accent = SECTORS.get(sector, SECTORS["default"])["accent"]

        from app.services.asset_factory import _MOCK_TEMPLATES, _MOCK_CSS, _MOCK_JS
        idx_tmpl = _MOCK_TEMPLATES.get("index", "<html></html>")
        slug = re.sub(r"[^a-z0-9-]", "-", keyword.lower()).strip("-")
        html = idx_tmpl.format(
            title=title, slug=slug, keyword=keyword, keyword_short=keyword[:25],
            accent=accent, year=year, monetization="affiliates", asset_type="landing_page",
        )
        return AIResponse(text=html, provider="mock", model="free-v3", tokens_used=1500, cost_est=0.0)

    def _mock_css(self, _prompt: str) -> AIResponse:
        from app.services.asset_factory import _MOCK_CSS
        css = _MOCK_CSS.format(accent="#3b82f6")
        return AIResponse(text=css, provider="mock", model="free-v3", tokens_used=600, cost_est=0.0)

    def _mock_blog_post(self, prompt: str) -> AIResponse:
        import re
        keyword = "producto"
        match = re.search(r'(?:sobre|about|keyword)[\s:]+["\']?([^"\'\n]{5,60})', prompt, re.IGNORECASE)
        if match:
            keyword = match.group(1).strip()
        title = keyword.replace("-", " ").title()
        post_title = f"Guía Completa de {title}"

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{post_title}</title>
<meta name="description" content="{post_title}. Artículo detallado con análisis, datos, y recomendaciones.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
body{{font-family:Inter,sans-serif;background:#0f172a;color:#e2e8f0;max-width:800px;margin:0 auto;padding:2rem;line-height:1.8}}
h1{{font-size:2.2rem;color:#3b82f6}}h2{{color:#94a3b8;margin-top:2rem}}p{{margin:1rem 0;color:#cbd5e1}}
</style>
</head>
<body>
<article>
<h1>{post_title}</h1>
<p><em>Publicado recientemente · 7 min de lectura</em></p>
<h2>Introducción</h2>
<p>El mercado de {keyword} ha experimentado un crecimiento notable. Cada vez más consumidores buscan información fiable antes de decidir, y esta guía nace para cubrir esa necesidad.</p>
<p>Hemos analizado docenas de opciones, consultado a expertos y recopilado opiniones reales para ofrecerte la información más completa.</p>
<h2>¿Qué hace especial a {title}?</h2>
<p>La calidad de los materiales, la atención al cliente y los precios competitivos convierten a {keyword} en una opción destacada frente a alternativas del mercado.</p>
<h2>Conclusión</h2>
<p>Después de un análisis exhaustivo, podemos afirmar que {title} representa la mejor relación calidad-precio disponible actualmente. Si estás considerando invertir en {keyword}, nuestra recomendación es clara.</p>
</article>
</body>
</html>"""
        return AIResponse(text=html, provider="mock", model="free-v3", tokens_used=800, cost_est=0.0)

    def _mock_generic(self, prompt: str) -> AIResponse:
        import re
        keyword = "producto"
        match = re.search(r'(?:keyword|sobre|topic)[\s:]+["\']?([^"\'\n]{3,60})', prompt, re.IGNORECASE)
        if match:
            keyword = match.group(1).strip()

        return AIResponse(
            text=json.dumps({
                "analysis": f"Análisis completado para '{keyword}'.",
                "score": random.randint(65, 95),
                "recommendation": random.choice(["ALTA", "MEDIA", "ALTA"]),
                "keywords": [keyword, f"mejor {keyword}", f"{keyword} precio", f"comprar {keyword}"],
                "estimated_cpc": round(random.uniform(0.15, 2.5), 2),
                "competition": random.choice(["baja", "media", "alta"]),
                "volume": random.randint(500, 50000),
            }, ensure_ascii=False, indent=2),
            provider="mock", model="free-v3", tokens_used=300, cost_est=0.0,
        )

    def _detect_sector(self, keyword: str) -> str:
        kw = keyword.lower()
        sector_keywords = {
            "tech": ["software", "app", "móvil", "smartphone", "portátil", "gaming", "auricular", "robot", "drone", "cámara", "monitor", "teclado"],
            "health": ["salud", "colchón", "vitamina", "suplemento", "fitness", "ejercicio", "dieta", "medicina", "masaje", "yoga"],
            "finance": ["inversión", "cripto", "bitcoin", "forex", "trading", "finanzas", "seguro", "hipoteca", "préstamo", "banco"],
            "ecommerce": ["mejor", "precio", "barato", "oferta", "descuento", "comprar", "tienda", "online", "envío", "calidad"],
            "education": ["curso", "aprender", "máster", "universidad", "certificación", "idioma", "inglés", "programación", "bootcamp"],
            "travel": ["viaje", "hotel", "vuelo", "destino", "vacaciones", "turismo", "playa", "montaña", "escapada", "resort"],
            "realestate": ["casa", "piso", "alquiler", "compra", "inmobiliaria", "hipoteca", "vivienda", "chalet", "ático", "terreno"],
        }
        for sector, words in sector_keywords.items():
            if any(w in kw for w in words):
                return sector
        return "default"


# ─────────────────────────────────────────────────────────────────────────────
# Provider Factory — automatic fallback chain
# ─────────────────────────────────────────────────────────────────────────────

_provider_cache: Optional[AIProvider] = None
_provider_chain: list[AIProvider] = []


def get_provider() -> AIProvider:
    """Returns the best available AI provider with automatic fallback."""
    global _provider_cache, _provider_chain

    if _provider_cache is not None:
        return _provider_cache

    # In SIMULATE_AI mode, always use mock
    if settings.SIMULATE_AI:
        _provider_cache = FreeProvider()
        logger.info("🎭 AI Provider: SIMULATE_AI → FreeProvider (mock)")
        return _provider_cache

    # Build fallback chain
    providers: list[AIProvider] = []

    # DeepSeek first if available (cheaper)
    ds = DeepSeekProvider()
    if ds.available:
        providers.append(ds)

    # Anthropic as fallback (or primary if DeepSeek not available)
    ant = AnthropicProvider()
    if ant.available:
        providers.append(ant)

    # Free provider always available as last resort
    providers.append(FreeProvider())

    _provider_chain = providers
    _provider_cache = providers[0]
    logger.info(f"🔌 AI Provider chain: {' → '.join(type(p).__name__ for p in providers)}")
    return _provider_cache


async def generate_with_fallback(
    prompt: str,
    system: str = "",
    max_tokens: int = 4000,
    temperature: float = 0.7,
) -> AIResponse:
    """Generate with automatic fallback through the provider chain."""
    global _provider_chain

    # In SIMULATE_AI mode, always use FreeProvider
    if settings.SIMULATE_AI:
        provider = FreeProvider()
        resp = await provider.generate(prompt, system, max_tokens, temperature)
        logger.info(f"🎭 AI response from mock ({resp.tokens_used} tokens)")
        return resp

    # Build chain if not already built
    if not _provider_chain:
        get_provider()

    # If chain still empty (no real providers configured), fall back to FreeProvider
    if not _provider_chain:
        provider = FreeProvider()
        resp = await provider.generate(prompt, system, max_tokens, temperature)
        return resp

    last_error = None
    for provider in _provider_chain:
        try:
            resp = await provider.generate(prompt, system, max_tokens, temperature)
            logger.info(f"✅ AI response from {resp.provider} ({resp.tokens_used} tokens, €{resp.cost_est:.5f})")
            return resp
        except Exception as e:
            logger.warning(f"⚠️  {type(provider).__name__} failed: {e}")
            last_error = e
            continue

    raise RuntimeError(f"All AI providers failed. Last error: {last_error}")


def reset_provider():
    """Reset provider cache (useful after config changes)."""
    global _provider_cache, _provider_chain
    _provider_cache = None
    _provider_chain = []
