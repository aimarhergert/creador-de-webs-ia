from datetime import datetime
from sqlalchemy import Float, DateTime, Integer, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Metrics(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), index=True)
    date: Mapped[datetime] = mapped_column(Date, default=datetime.utcnow)
    visits: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    bounce_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_session_duration: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asset: Mapped["Asset"] = relationship(back_populates="metrics")

    @property
    def conversion_rate(self) -> float:
        if self.visits == 0:
            return 0.0
        return round((self.conversions / self.visits) * 100, 2)

    @property
    def roi(self) -> float:
        if self.cost == 0:
            return 0.0
        return round(self.revenue / self.cost, 2)
