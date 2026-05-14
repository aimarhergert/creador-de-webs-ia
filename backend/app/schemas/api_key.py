from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    expires_at: Optional[datetime] = None


class ApiKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreated(ApiKeyOut):
    """Returned only on creation — plaintext key never stored again."""
    plaintext_key: str
