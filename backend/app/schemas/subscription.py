from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.subscription import SubscriptionPlan, SubscriptionStatus, PLAN_CONFIG


class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    plan: SubscriptionPlan
    status: SubscriptionStatus
    stripe_subscription_id: Optional[str]
    stripe_customer_id: Optional[str]
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    assets_limit: int
    strategies_limit: int
    price_eur: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanInfo(BaseModel):
    plan: str
    label: str
    price_eur: int
    assets_limit: int
    strategies_limit: int
    features: list[str]


def get_all_plans() -> list[PlanInfo]:
    features_map = {
        "free":         ["3 activos/mes", "1 estrategia", "Simulación básica"],
        "starter":      ["10 activos/mes", "2 estrategias", "Analytics completo", "Soporte email"],
        "professional": ["50 activos/mes", "4 estrategias", "AI Decision Engine", "API access", "Soporte prioritario"],
        "enterprise":   ["Ilimitado", "6 estrategias", "Admin panel", "Custom AI params", "Soporte dedicado"],
    }
    return [
        PlanInfo(
            plan=plan,
            label=cfg["label"],
            price_eur=cfg["price_eur"],
            assets_limit=cfg["assets"],
            strategies_limit=cfg["strategies"],
            features=features_map.get(plan, []),
        )
        for plan, cfg in PLAN_CONFIG.items()
    ]
