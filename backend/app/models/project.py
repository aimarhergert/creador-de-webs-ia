import enum
from datetime import datetime
from sqlalchemy import String, Float, Boolean, Enum as SAEnum, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    strategy_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("strategies.id"), nullable=True, index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, native_enum=False), default=ProjectStatus.ACTIVE
    )

    total_budget: Mapped[float] = mapped_column(Float, default=0.0)
    spent_budget: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="projects", lazy="select")
    strategy: Mapped["Strategy | None"] = relationship(back_populates="projects", lazy="select")
    assets: Mapped[list["Asset"]] = relationship(back_populates="project", lazy="select")
    investments: Mapped[list["Investment"]] = relationship(back_populates="project", lazy="select")

    @property
    def total_revenue(self) -> float:
        return round(sum(a.revenue for a in self.assets), 2)

    @property
    def roi(self) -> float:
        if self.spent_budget == 0:
            return 0.0
        return round(self.total_revenue / self.spent_budget, 2)
