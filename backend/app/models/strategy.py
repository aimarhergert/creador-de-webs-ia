import enum
from datetime import datetime
from sqlalchemy import String, Float, Boolean, Enum as SAEnum, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class StrategyType(str, enum.Enum):
    SEO_GROWTH = "seo_growth"
    AFFILIATE_ARBITRAGE = "affiliate_arbitrage"
    LEAD_GENERATION = "lead_generation"
    MICRO_SAAS = "micro_saas"
    AGGRESSIVE_SCALING = "aggressive_scaling"
    CONSERVATIVE_ROI = "conservative_roi"


# Default parameters per strategy type — used by simulation engine and seeder
STRATEGY_PRESETS: dict[str, dict] = {
    "seo_growth": {
        "visits_min": 8, "visits_max": 60,
        "conversion_rate_min": 0.03, "conversion_rate_max": 0.07,
        "revenue_per_conversion_min": 15.0, "revenue_per_conversion_max": 80.0,
        "scaling_multiplier": 2.5, "kill_threshold_roi": 0.8, "scale_threshold_roi": 3.0,
        "monthly_budget": 300.0, "capital_allocation_pct": 0.15,
        "color": "green", "icon": "🌱",
        "description": "Tráfico orgánico sostenible a largo plazo. Bajo riesgo, crecimiento constante.",
    },
    "affiliate_arbitrage": {
        "visits_min": 15, "visits_max": 80,
        "conversion_rate_min": 0.04, "conversion_rate_max": 0.09,
        "revenue_per_conversion_min": 20.0, "revenue_per_conversion_max": 120.0,
        "scaling_multiplier": 3.0, "kill_threshold_roi": 1.2, "scale_threshold_roi": 3.5,
        "monthly_budget": 500.0, "capital_allocation_pct": 0.20,
        "color": "orange", "icon": "🔗",
        "description": "Arbitraje de márgenes en programas de afiliados. ROI agresivo.",
    },
    "lead_generation": {
        "visits_min": 10, "visits_max": 50,
        "conversion_rate_min": 0.05, "conversion_rate_max": 0.12,
        "revenue_per_conversion_min": 8.0, "revenue_per_conversion_max": 35.0,
        "scaling_multiplier": 2.0, "kill_threshold_roi": 0.9, "scale_threshold_roi": 2.8,
        "monthly_budget": 400.0, "capital_allocation_pct": 0.18,
        "color": "blue", "icon": "📧",
        "description": "Captura de leads cualificados. Ingresos predecibles por volumen.",
    },
    "micro_saas": {
        "visits_min": 5, "visits_max": 30,
        "conversion_rate_min": 0.02, "conversion_rate_max": 0.06,
        "revenue_per_conversion_min": 29.0, "revenue_per_conversion_max": 199.0,
        "scaling_multiplier": 4.0, "kill_threshold_roi": 0.7, "scale_threshold_roi": 2.5,
        "monthly_budget": 600.0, "capital_allocation_pct": 0.25,
        "color": "purple", "icon": "⚙️",
        "description": "Ingresos recurrentes (MRR) de productos SaaS nicho. Alto LTV.",
    },
    "aggressive_scaling": {
        "visits_min": 30, "visits_max": 150,
        "conversion_rate_min": 0.02, "conversion_rate_max": 0.08,
        "revenue_per_conversion_min": 10.0, "revenue_per_conversion_max": 90.0,
        "scaling_multiplier": 5.0, "kill_threshold_roi": 1.5, "scale_threshold_roi": 4.0,
        "monthly_budget": 1000.0, "capital_allocation_pct": 0.35,
        "color": "red", "icon": "🚀",
        "description": "Máximo volumen y velocidad. Alta varianza — alto upside.",
    },
    "conservative_roi": {
        "visits_min": 5, "visits_max": 25,
        "conversion_rate_min": 0.04, "conversion_rate_max": 0.08,
        "revenue_per_conversion_min": 12.0, "revenue_per_conversion_max": 60.0,
        "scaling_multiplier": 1.5, "kill_threshold_roi": 0.6, "scale_threshold_roi": 2.0,
        "monthly_budget": 200.0, "capital_allocation_pct": 0.10,
        "color": "slate", "icon": "🛡️",
        "description": "Preservación de capital. Crecimiento lineal y estable.",
    },
}


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[StrategyType] = mapped_column(SAEnum(StrategyType, native_enum=False), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Simulation parameters
    visits_min: Mapped[int] = mapped_column(Integer, default=5)
    visits_max: Mapped[int] = mapped_column(Integer, default=50)
    conversion_rate_min: Mapped[float] = mapped_column(Float, default=0.01)
    conversion_rate_max: Mapped[float] = mapped_column(Float, default=0.05)
    revenue_per_conversion_min: Mapped[float] = mapped_column(Float, default=5.0)
    revenue_per_conversion_max: Mapped[float] = mapped_column(Float, default=50.0)
    scaling_multiplier: Mapped[float] = mapped_column(Float, default=3.0)
    kill_threshold_roi: Mapped[float] = mapped_column(Float, default=1.0)
    scale_threshold_roi: Mapped[float] = mapped_column(Float, default=3.0)

    # Budget
    monthly_budget: Mapped[float] = mapped_column(Float, default=500.0)
    capital_allocation_pct: Mapped[float] = mapped_column(Float, default=0.20)

    # UI
    color: Mapped[str | None] = mapped_column(String(20))
    icon: Mapped[str | None] = mapped_column(String(10))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    assets: Mapped[list["Asset"]] = relationship(back_populates="strategy", lazy="select")
    projects: Mapped[list["Project"]] = relationship(back_populates="strategy", lazy="select")
    optimization_logs: Mapped[list["OptimizationLog"]] = relationship(
        back_populates="strategy", lazy="select"
    )
