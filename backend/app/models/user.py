import enum
from datetime import datetime
from sqlalchemy import String, Boolean, Enum as SAEnum, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, enum.Enum):
    INVESTOR = "investor"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False), default=UserRole.INVESTOR
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    wallet: Mapped["Wallet"] = relationship(back_populates="user", uselist=False, lazy="selectin")
    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )
    activity_events: Mapped[list["ActivityEvent"]] = relationship(
        back_populates="user", lazy="dynamic"
    )
    assets: Mapped[list["Asset"]] = relationship(back_populates="user", lazy="select")
    projects: Mapped[list["Project"]] = relationship(back_populates="user", lazy="select")
    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="user", lazy="select")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user", lazy="select")
