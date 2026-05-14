"""WebScan model — stores external website analysis results."""

from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class WebScan(Base):
    __tablename__ = "web_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    status_code: Mapped[int] = mapped_column(Integer, default=0)

    seo_score: Mapped[int] = mapped_column(Integer, default=0)
    content_score: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    title: Mapped[str | None] = mapped_column(String(500))
    meta_description: Mapped[str | None] = mapped_column(String(500))
    top_keywords: Mapped[str | None] = mapped_column(Text)  # JSON array
    estimated_traffic: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cpc: Mapped[float] = mapped_column(Float, default=0.0)
    content_type: Mapped[str | None] = mapped_column(String(50))

    ai_insights: Mapped[str | None] = mapped_column(Text)
    recommendations: Mapped[str | None] = mapped_column(Text)  # JSON array
    raw_data: Mapped[str | None] = mapped_column(Text)  # JSON

    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
