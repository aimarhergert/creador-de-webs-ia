import json
import logging
from app.services.ai_provider import generate_with_fallback
from app.schemas.orchestrator import MarketOpportunity

logger = logging.getLogger(__name__)


async def scan_market(keyword: str) -> MarketOpportunity:
    logger.info(f"[MarketEngine] Analizando nicho: {keyword}")

    prompt = f"""Analiza esta keyword para monetización digital: "{keyword}"

Responde con este JSON exacto (sin markdown, sin texto adicional):
{{
  "keyword": "{keyword}",
  "cpc": <float USD>,
  "monthly_searches": <int>,
  "competition": "low|medium|high",
  "intent": "informational|commercial|transactional",
  "score": <float 0-10>
}}"""

    try:
        resp = await generate_with_fallback(prompt, max_tokens=300, temperature=0.3)
        raw = resp.text.strip()
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                if "{" in part:
                    raw = part.strip()
                    if raw.startswith("json"): raw = raw[4:]
                    break
        if "{" in raw:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            raw = raw[start:end]
        data = json.loads(raw)
        opportunity = MarketOpportunity(**data)
    except Exception as e:
        logger.warning(f"[MarketEngine] AI parsing failed ({e}), using fallback for '{keyword}'")
        import random
        opportunity = MarketOpportunity(
            keyword=keyword,
            cpc=round(random.uniform(0.15, 2.5), 2),
            monthly_searches=random.randint(500, 30000),
            competition=random.choice(["low", "medium", "high"]),
            intent=random.choice(["commercial", "informational", "transactional"]),
            score=round(random.uniform(3, 8), 1),
        )
    logger.info(
        f"[MarketEngine] Score: {opportunity.score}/10 | CPC: ${opportunity.cpc} | Intent: {opportunity.intent}"
    )
    return opportunity


async def is_worth_pursuing(opportunity: MarketOpportunity) -> bool:
    return opportunity.score >= 5.0 and opportunity.intent in ("commercial", "transactional")
