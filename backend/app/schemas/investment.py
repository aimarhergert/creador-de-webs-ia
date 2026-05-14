from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.investment import InvestmentStatus


class InvestmentCreate(BaseModel):
    asset_id: Optional[int] = None
    strategy_id: Optional[int] = None
    project_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    notes: Optional[str] = None


class InvestmentOut(BaseModel):
    id: int
    wallet_id: int
    asset_id: Optional[int]
    strategy_id: Optional[int]
    project_id: Optional[int]
    amount: float
    returned_amount: float
    roi: float
    pnl: float
    status: InvestmentStatus
    notes: Optional[str]
    allocated_at: datetime
    closed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class InvestmentListOut(BaseModel):
    total: int
    items: list[InvestmentOut]


class InvestmentSummary(BaseModel):
    total_invested: float
    total_returned: float
    active_count: int
    total_count: int
    portfolio_roi: float
    portfolio_pnl: float
    by_strategy: dict[str, float]
