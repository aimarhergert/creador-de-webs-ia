import enum
import json
from datetime import datetime
from sqlalchemy import String, Float, Enum as SAEnum, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AssetType(str, enum.Enum):
    LANDING_PAGE = "landing_page"
    BLOG = "blog"
    ECOMMERCE = "ecommerce"
    LEAD_GEN = "lead_gen"


class AssetStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    CREATED = "created"
    DEPLOYING = "deploying"
    LIVE = "live"
    OPTIMIZING = "optimizing"
    SCALING = "scaling"
    KILLED = "killed"
    ERROR = "error"


class MonetizationModel(str, enum.Enum):
    AFFILIATES = "affiliates"
    ADS = "ads"
    ECOMMERCE = "ecommerce"
    LEADS = "leads"
    NONE = "none"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    keyword: Mapped[str] = mapped_column(String(255), index=True)

    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    strategy_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("strategies.id"), nullable=True, index=True
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True, index=True
    )

    type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, native_enum=False), default=AssetType.LANDING_PAGE
    )
    status: Mapped[AssetStatus] = mapped_column(
        SAEnum(AssetStatus, native_enum=False), default=AssetStatus.PENDING
    )
    monetization_model: Mapped[MonetizationModel] = mapped_column(
        SAEnum(MonetizationModel, native_enum=False), default=MonetizationModel.NONE
    )

    url: Mapped[str | None] = mapped_column(String(500))
    repo_name: Mapped[str | None] = mapped_column(String(255))
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    market_score: Mapped[float] = mapped_column(Float, default=0.0)
    cpc_estimate: Mapped[float] = mapped_column(Float, default=0.0)

    content_html: Mapped[str | None] = mapped_column(Text)
    content_files: Mapped[str | None] = mapped_column(Text)  # JSON: {filename: content}
    error_message: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User | None"] = relationship(back_populates="assets", lazy="select")
    strategy: Mapped["Strategy | None"] = relationship(back_populates="assets", lazy="select")
    project: Mapped["Project | None"] = relationship(back_populates="assets", lazy="select")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="asset", lazy="selectin")
    metrics: Mapped[list["Metrics"]] = relationship(back_populates="asset", lazy="selectin")
    optimization_logs: Mapped[list["OptimizationLog"]] = relationship(
        back_populates="asset", lazy="select"
    )
    traffic_simulation: Mapped["TrafficSimulation | None"] = relationship(
        back_populates="asset", uselist=False, lazy="select"
    )
    investments: Mapped[list["Investment"]] = relationship(back_populates="asset", lazy="select")
    blog_posts: Mapped[list["BlogPost"]] = relationship(back_populates="asset", lazy="select")

    @property
    def roi(self) -> float:
        if self.cost == 0:
            return 0.0
        return round(self.revenue / self.cost, 2)

    @property
    def files(self) -> dict[str, str]:
        if not self.content_files:
            return {}
        try:
            return json.loads(self.content_files)
        except (json.JSONDecodeError, TypeError):
            return {}
