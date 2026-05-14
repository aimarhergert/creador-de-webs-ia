import enum
from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EventType(str, enum.Enum):
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_DONE = "pipeline_done"
    PIPELINE_ERROR = "pipeline_error"
    ASSET_LIVE = "asset_live"
    ASSET_KILLED = "asset_killed"
    REVENUE_EARNED = "revenue_earned"
    TRAFFIC_SPIKE = "traffic_spike"
    ROI_UPDATED = "roi_updated"
    WALLET_DEPOSIT = "wallet_deposit"
    WALLET_ALLOCATION = "wallet_allocation"
    OPTIMIZATION_RUN = "optimization_run"
    SCALE_TRIGGERED = "scale_triggered"
    SIMULATION_TICK = "simulation_tick"
    USER_LOGIN = "user_login"


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True, index=True)
    event_type: Mapped[EventType] = mapped_column(
        SAEnum(EventType, native_enum=False), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    data: Mapped[dict | None] = mapped_column(JSON)  # extra payload
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user: Mapped["User"] = relationship(back_populates="activity_events")
