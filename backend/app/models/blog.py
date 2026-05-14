"""
Blog System — standalone or integrated blog posts.
Users can generate blog articles via AI and manage them.
"""

import enum
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, Boolean, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BlogStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    excerpt: Mapped[str | None] = mapped_column(Text)
    content_html: Mapped[str | None] = mapped_column(Text)
    content_markdown: Mapped[str | None] = mapped_column(Text)

    cover_image: Mapped[str | None] = mapped_column(String(500))
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    tags: Mapped[str | None] = mapped_column(Text)  # JSON array of strings
    sector: Mapped[str | None] = mapped_column(String(50))  # tech, health, etc.

    status: Mapped[BlogStatus] = mapped_column(
        SAEnum(BlogStatus, native_enum=False), default=BlogStatus.DRAFT, index=True
    )

    # SEO
    meta_title: Mapped[str | None] = mapped_column(String(200))
    meta_description: Mapped[str | None] = mapped_column(String(500))
    focus_keyword: Mapped[str | None] = mapped_column(String(200))

    # Metrics (if published as standalone page)
    views: Mapped[int] = mapped_column(Integer, default=0)
    seo_score: Mapped[int | None] = mapped_column(Integer)

    # Relations
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("projects.id"), nullable=True)

    is_standalone: Mapped[bool] = mapped_column(Boolean, default=False)
    # When True: hosted at /blog/{slug}. When False: embedded in asset page.

    generated_by: Mapped[str | None] = mapped_column(String(50))  # "anthropic", "deepseek", "mock"

    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    asset = relationship("Asset", back_populates="blog_posts", lazy="selectin")
