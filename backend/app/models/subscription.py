import enum
from datetime import datetime
from sqlalchemy import String, Boolean, Enum as SAEnum, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INACTIVE = "inactive"


PLAN_CONFIG: dict[str, dict] = {
    "free":         {"assets": 3,   "strategies": 1, "price_eur": 0,   "label": "Free"},
    "starter":      {"assets": 10,  "strategies": 2, "price_eur": 49,  "label": "Starter"},
    "professional": {"assets": 50,  "strategies": 4, "price_eur": 149, "label": "Professional"},
    "enterprise":   {"assets": 999, "strategies": 6, "price_eur": 499, "label": "Enterprise"},
}


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True)

    plan: Mapped[SubscriptionPlan] = mapped_column(
        SAEnum(SubscriptionPlan, native_enum=False), default=SubscriptionPlan.FREE
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, native_enum=False), default=SubscriptionStatus.ACTIVE
    )

    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    current_period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)

    assets_limit: Mapped[int] = mapped_column(Integer, default=3)
    strategies_limit: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="subscription", lazy="select")

    @property
    def price_eur(self) -> int:
        return PLAN_CONFIG.get(self.plan.value, {}).get("price_eur", 0)

    @property
    def is_active(self) -> bool:
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)
