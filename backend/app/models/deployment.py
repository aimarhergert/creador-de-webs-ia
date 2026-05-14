import enum
from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DeploymentPlatform(str, enum.Enum):
    VERCEL = "vercel"
    GITHUB_PAGES = "github_pages"
    AWS_S3 = "aws_s3"
    LOCAL = "local"


class DeploymentStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), index=True)
    platform: Mapped[DeploymentPlatform] = mapped_column(SAEnum(DeploymentPlatform, native_enum=False))
    url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[DeploymentStatus] = mapped_column(
        SAEnum(DeploymentStatus, native_enum=False), default=DeploymentStatus.PENDING
    )
    deploy_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asset: Mapped["Asset"] = relationship(back_populates="deployments")
