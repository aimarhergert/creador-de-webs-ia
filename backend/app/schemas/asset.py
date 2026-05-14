from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.asset import AssetType, AssetStatus, MonetizationModel


class AssetCreate(BaseModel):
    keyword: str = Field(..., min_length=3, max_length=255)
    type: AssetType = AssetType.LANDING_PAGE
    monetization_model: MonetizationModel = MonetizationModel.AFFILIATES


class AssetUpdate(BaseModel):
    status: Optional[AssetStatus] = None
    revenue: Optional[float] = None
    cost: Optional[float] = None
    url: Optional[str] = None


class GenerateRequest(BaseModel):
    keyword: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Keyword, nicho o descripción del negocio a generar",
        examples=["best ergonomic office chair", "academia de inglés online Madrid"],
    )
    type: AssetType = Field(default=AssetType.LANDING_PAGE)
    monetization_model: MonetizationModel = Field(default=MonetizationModel.AFFILIATES)


class MetricsOut(BaseModel):
    id: int
    date: datetime
    visits: int
    conversions: int
    revenue: float
    cost: float
    conversion_rate: float
    roi: float

    model_config = {"from_attributes": True}


class DeploymentOut(BaseModel):
    id: int
    platform: str
    url: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetOut(BaseModel):
    id: int
    keyword: str
    type: AssetType
    url: Optional[str]
    revenue: float
    cost: float
    roi: float
    status: AssetStatus
    monetization_model: MonetizationModel
    market_score: float
    cpc_estimate: float
    created_at: datetime
    updated_at: datetime
    deployments: List[DeploymentOut] = []
    metrics: List[MetricsOut] = []

    model_config = {"from_attributes": True}


class AssetWithFilesOut(AssetOut):
    """Extended response used by /generate — includes the raw generated files."""
    files: dict[str, str] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class AssetListOut(BaseModel):
    total: int
    items: List[AssetOut]
