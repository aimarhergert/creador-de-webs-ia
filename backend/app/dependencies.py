from typing import Optional
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def require_api_key(api_key: str = Security(_api_key_header)) -> str:
    if settings.DEMO_MODE or not settings.AROS_API_KEY:
        return ""
    if api_key != settings.AROS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o ausente. Incluye el header 'X-API-Key: <tu_clave>'.",
        )
    return api_key


async def get_current_user(
    token: Optional[str] = Depends(_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.services.auth_service import decode_token, get_user_by_id
    from app.models.user import User

    # Demo mode — bypass all auth
    if settings.DEMO_MODE:
        from sqlalchemy import select
        from app.models.user import User
        from app.models.wallet import Wallet
        from app.services.auth_service import hash_password
        r = await db.execute(select(User).where(User.email == "demo@aros.ai"))
        user = r.scalar_one_or_none()
        if user:
            # Ensure wallet exists
            wr = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
            if not wr.scalar_one_or_none():
                w = Wallet(user_id=user.id, balance=1000.0, total_deposited=1000.0)
                db.add(w)
                await db.commit()
            return user
        demo = User(
            email="demo@aros.ai",
            username="demo_investor",
            hashed_password=hash_password("demo123"),
            full_name="Demo Investor",
            role="admin",
            is_active=True,
        )
        db.add(demo)
        await db.flush()
        w = Wallet(user_id=demo.id, balance=1000.0, total_deposited=1000.0)
        db.add(w)
        await db.commit()
        await db.refresh(demo)
        return demo

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exc
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = await get_user_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise credentials_exc
    return user


async def get_current_admin(current_user=Depends(get_current_user)):
    from app.models.user import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Returns user if authenticated, None otherwise (for public endpoints)."""
    if not token:
        return None
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None
