"""Industry sector definitions — affects strategy parameters and asset generation."""

import enum
from datetime import datetime
from sqlalchemy import String, Float, Boolean, Enum as SAEnum, DateTime, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SectorEnum(str, enum.Enum):
    TECH = "tech"
    HEALTH = "health"
    FINANCE = "finance"
    ECOMMERCE = "ecommerce"
    EDUCATION = "education"
    TRAVEL = "travel"
    REALESTATE = "realestate"
    OTHER = "other"


# Preset sectors with simulation modifiers
SECTOR_PRESETS: dict[str, dict] = {
    "tech": {
        "name": "Tecnología", "icon": "💻",
        "visits_multiplier": 1.3, "conversion_multiplier": 0.8,
        "avg_cpc": 1.20, "revenue_multiplier": 1.5,
        "description": "Alta demanda, CPC elevado, buen margen en afiliados.",
        "color": "blue",
    },
    "health": {
        "name": "Salud y Bienestar", "icon": "🏥",
        "visits_multiplier": 1.5, "conversion_multiplier": 1.1,
        "avg_cpc": 0.80, "revenue_multiplier": 1.2,
        "description": "Tráfico masivo, conversión media, nicho muy rentable.",
        "color": "green",
    },
    "finance": {
        "name": "Finanzas", "icon": "💰",
        "visits_multiplier": 0.9, "conversion_multiplier": 1.4,
        "avg_cpc": 2.50, "revenue_multiplier": 2.0,
        "description": "CPC alto, conversiones muy valiosas, alta rentabilidad por lead.",
        "color": "purple",
    },
    "ecommerce": {
        "name": "E-Commerce", "icon": "🛒",
        "visits_multiplier": 1.4, "conversion_multiplier": 0.9,
        "avg_cpc": 0.60, "revenue_multiplier": 1.0,
        "description": "Tráfico elevado, márgenes ajustados, volumen de ventas.",
        "color": "amber",
    },
    "education": {
        "name": "Educación", "icon": "📚",
        "visits_multiplier": 1.0, "conversion_multiplier": 1.2,
        "avg_cpc": 1.50, "revenue_multiplier": 1.8,
        "description": "Conversiones estables, alto valor por lead, recurrencia.",
        "color": "sky",
    },
    "travel": {
        "name": "Viajes y Turismo", "icon": "✈️",
        "visits_multiplier": 1.2, "conversion_multiplier": 1.0,
        "avg_cpc": 0.90, "revenue_multiplier": 1.3,
        "description": "Estacional pero alto volumen. Comisiones atractivas.",
        "color": "pink",
    },
    "realestate": {
        "name": "Inmobiliario", "icon": "🏠",
        "visits_multiplier": 0.7, "conversion_multiplier": 1.5,
        "avg_cpc": 3.00, "revenue_multiplier": 3.0,
        "description": "Tráfico nicho, conversiones de muy alto valor.",
        "color": "lime",
    },
    "other": {
        "name": "General", "icon": "🌐",
        "visits_multiplier": 1.0, "conversion_multiplier": 1.0,
        "avg_cpc": 1.00, "revenue_multiplier": 1.0,
        "description": "Parámetros equilibrados para cualquier nicho.",
        "color": "gray",
    },
}


class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[SectorEnum] = mapped_column(SAEnum(SectorEnum, native_enum=False), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(10), default="🌐")
    description: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(20), default="blue")

    # Simulation modifiers
    visits_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    conversion_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    avg_cpc: Mapped[float] = mapped_column(Float, default=1.0)
    revenue_multiplier: Mapped[float] = mapped_column(Float, default=1.0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
