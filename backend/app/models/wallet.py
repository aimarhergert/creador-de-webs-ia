import enum
from datetime import datetime
from sqlalchemy import String, Float, Enum as SAEnum, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ALLOCATION = "allocation"
    RETURN = "return"
    FEE = "fee"


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    total_deposited: Mapped[float] = mapped_column(Float, default=0.0)
    total_invested: Mapped[float] = mapped_column(Float, default=0.0)
    total_returned: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="wallet")
    transactions: Mapped[list["WalletTransaction"]] = relationship(
        back_populates="wallet", lazy="selectin", order_by="WalletTransaction.created_at.desc()"
    )
    investments: Mapped[list["Investment"]] = relationship(back_populates="wallet", lazy="select")

    @property
    def roi(self) -> float:
        if self.total_invested == 0:
            return 0.0
        return round(((self.total_returned - self.total_invested) / self.total_invested) * 100, 2)

    @property
    def pnl(self) -> float:
        return round(self.total_returned - self.total_invested, 2)


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(Integer, ForeignKey("wallets.id"), index=True)
    type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, native_enum=False), nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")
