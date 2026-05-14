from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.project import ProjectStatus
from app.schemas.asset import AssetOut


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    strategy_id: Optional[int] = None
    total_budget: float = Field(default=0.0, ge=0.0)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    strategy_id: Optional[int] = None
    total_budget: Optional[float] = None


class ProjectOut(BaseModel):
    id: int
    user_id: int
    strategy_id: Optional[int]
    name: str
    description: Optional[str]
    status: ProjectStatus
    total_budget: float
    spent_budget: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetailOut(ProjectOut):
    assets: list[AssetOut] = []


class ProjectListOut(BaseModel):
    total: int
    items: list[ProjectOut]
