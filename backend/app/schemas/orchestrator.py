from pydantic import BaseModel, Field
from typing import Optional
from app.models.asset import AssetType, MonetizationModel


class PipelineRequest(BaseModel):
    keyword: str = Field(..., min_length=3, description="Keyword/nicho objetivo")
    type: AssetType = AssetType.LANDING_PAGE
    monetization_model: MonetizationModel = MonetizationModel.AFFILIATES
    async_mode: bool = Field(default=True, description="True = Celery task, False = síncrono")


class PipelineResponse(BaseModel):
    asset_id: Optional[int] = None
    task_id: Optional[str] = None
    status: str
    message: str


class MarketOpportunity(BaseModel):
    keyword: str
    cpc: float
    monthly_searches: int
    competition: str
    intent: str
    score: float
