from datetime import datetime
from sqlalchemy import Float, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TrafficSimulation(Base):
    __tablename__ = "traffic_simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), unique=True, index=True)

    # Per-tick configuration (overrides strategy defaults)
    base_visits_per_tick: Mapped[int] = mapped_column(Integer, default=10)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.03)
    revenue_per_conversion: Mapped[float] = mapped_column(Float, default=15.0)
    growth_rate: Mapped[float] = mapped_column(Float, default=0.05)
    volatility: Mapped[float] = mapped_column(Float, default=0.20)

    # Cumulative state
    total_visits: Mapped[int] = mapped_column(Integer, default=0)
    total_conversions: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # Control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tick_count: Mapped[int] = mapped_column(Integer, default=0)
    last_tick_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    asset: Mapped["Asset"] = relationship(back_populates="traffic_simulation", lazy="select")
