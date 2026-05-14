from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.strategy import StrategyType


class StrategyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    type: StrategyType
    description: Optional[str] = None
    visits_min: int = Field(default=5, ge=1)
    visits_max: int = Field(default=50, ge=1)
    conversion_rate_min: float = Field(default=0.01, ge=0.001, le=1.0)
    conversion_rate_max: float = Field(default=0.05, ge=0.001, le=1.0)
    revenue_per_conversion_min: float = Field(default=5.0, ge=0.0)
    revenue_per_conversion_max: float = Field(default=50.0, ge=0.0)
    scaling_multiplier: float = Field(default=3.0, ge=1.0)
    kill_threshold_roi: float = Field(default=1.0, ge=0.0)
    scale_threshold_roi: float = Field(default=3.0, ge=1.0)
    monthly_budget: float = Field(default=500.0, ge=0.0)
    capital_allocation_pct: float = Field(default=0.20, ge=0.01, le=1.0)
    color: Optional[str] = None
    icon: Optional[str] = None


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    visits_min: Optional[int] = None
    visits_max: Optional[int] = None
    conversion_rate_min: Optional[float] = None
    conversion_rate_max: Optional[float] = None
    revenue_per_conversion_min: Optional[float] = None
    revenue_per_conversion_max: Optional[float] = None
    scaling_multiplier: Optional[float] = None
    kill_threshold_roi: Optional[float] = None
    scale_threshold_roi: Optional[float] = None
    monthly_budget: Optional[float] = None
    capital_allocation_pct: Optional[float] = None


class StrategyOut(BaseModel):
    id: int
    name: str
    type: StrategyType
    description: Optional[str]
    is_preset: bool
    is_active: bool
    user_id: Optional[int]
    visits_min: int
    visits_max: int
    conversion_rate_min: float
    conversion_rate_max: float
    revenue_per_conversion_min: float
    revenue_per_conversion_max: float
    scaling_multiplier: float
    kill_threshold_roi: float
    scale_threshold_roi: float
    monthly_budget: float
    capital_allocation_pct: float
    color: Optional[str]
    icon: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class StrategyListOut(BaseModel):
    total: int
    items: list[StrategyOut]
