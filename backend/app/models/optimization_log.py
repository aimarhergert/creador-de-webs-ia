import enum
from datetime import datetime
from sqlalchemy import Float, Boolean, Enum as SAEnum, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OptimizationDecision(str, enum.Enum):
    SCALE = "scale"
    OPTIMIZE = "optimize"
    KILL = "kill"
    HOLD = "hold"
    WAIT = "wait"


class OptimizationLog(Base):
    __tablename__ = "optimization_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), index=True)
    strategy_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("strategies.id"), nullable=True, index=True
    )

    decision: Mapped[OptimizationDecision] = mapped_column(
        SAEnum(OptimizationDecision, native_enum=False), nullable=False, index=True
    )
    roi_at_decision: Mapped[float] = mapped_column(Float, default=0.0)
    revenue_at_decision: Mapped[float] = mapped_column(Float, default=0.0)
    cost_at_decision: Mapped[float] = mapped_column(Float, default=0.0)
    days_tracked: Mapped[int] = mapped_column(Integer, default=0)

    capital_before: Mapped[float] = mapped_column(Float, default=0.0)
    capital_after: Mapped[float] = mapped_column(Float, default=0.0)
    reasoning: Mapped[str | None] = mapped_column(Text)
    executed: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    asset: Mapped["Asset"] = relationship(back_populates="optimization_logs", lazy="select")
    strategy: Mapped["Strategy | None"] = relationship(back_populates="optimization_logs", lazy="select")
