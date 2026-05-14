from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.user import UserRole


class UserAdminOut(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAdminUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class SystemStats(BaseModel):
    total_users: int
    active_users: int
    total_assets: int
    live_assets: int
    scaling_assets: int
    killed_assets: int
    total_revenue: float
    total_events: int
    sim_ticks_today: int


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    ip_address: Optional[str]
    data: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
