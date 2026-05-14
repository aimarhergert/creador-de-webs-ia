import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.api_key import ApiKey
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyOut, ApiKeyCreated

router = APIRouter()

_PREFIX = "aros_"


def _generate_key() -> tuple[str, str, str]:
    """Returns (plaintext, hashed, prefix)."""
    import bcrypt
    raw = _PREFIX + secrets.token_urlsafe(32)
    hashed = bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()
    prefix = raw[:16]
    return raw, hashed, prefix


@router.get("", response_model=list[ApiKeyOut])
async def list_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == current_user.id, ApiKey.is_active == True)
    )
    return result.scalars().all()


@router.post("", response_model=ApiKeyCreated, status_code=201)
async def create_key(
    body: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plaintext, hashed, prefix = _generate_key()
    key = ApiKey(
        user_id=current_user.id,
        name=body.name,
        key_hash=hashed,
        key_prefix=prefix,
        expires_at=body.expires_at,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return ApiKeyCreated(
        **ApiKeyOut.model_validate(key).model_dump(),
        plaintext_key=plaintext,
    )


@router.delete("/{key_id}", status_code=204)
async def revoke_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key no encontrada")

    key.is_active = False
    await db.commit()
