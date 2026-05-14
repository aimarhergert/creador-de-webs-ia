import enum
from datetime import datetime
from sqlalchemy import Float, Enum as SAEnum, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class InvestmentStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    RETURNED = "returned"
    PARTIALLY_RETURNED = "partially_returned"
    LOST = "lost"


class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(Integer, ForeignKey("wallets.id"), index=True)
    asset_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("assets.id"), nullable=True, index=True
    )
    strategy_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("strategies.id"), nullable=True, index=True
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True, index=True
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    returned_amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[InvestmentStatus] = mapped_column(
        SAEnum(InvestmentStatus, native_enum=False), default=InvestmentStatus.PENDING
    )
    notes: Mapped[str | None] = mapped_column(Text)

    allocated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    wallet: Mapped["Wallet"] = relationship(back_populates="investments", lazy="select")
    asset: Mapped["Asset | None"] = relationship(back_populates="investments", lazy="select")
    project: Mapped["Project | None"] = relationship(back_populates="investments", lazy="select")

    @property
    def roi(self) -> float:
        if self.amount == 0:
            return 0.0
        return round(self.returned_amount / self.amount, 2)

    @property
    def pnl(self) -> float:
        return round(self.returned_amount - self.amount, 2)
