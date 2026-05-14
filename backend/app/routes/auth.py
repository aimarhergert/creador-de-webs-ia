from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.activity import ActivityEvent, EventType
from app.services.auth_service import (
    create_user, authenticate_user,
    create_access_token, create_refresh_token, decode_token,
    get_user_by_email,
)

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime
    wallet_balance: float = 0.0

    model_config = {"from_attributes": True}


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username ya en uso")

    user = await create_user(
        db, body.email, body.username, body.password, body.full_name
    )

    # Log activity
    db.add(ActivityEvent(
        user_id=user.id,
        event_type=EventType.USER_LOGIN,
        title="Nuevo inversor registrado",
        description=f"@{user.username} se unió a AROS",
    ))
    await db.commit()

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db.add(ActivityEvent(
        user_id=user.id,
        event_type=EventType.USER_LOGIN,
        title="Sesión iniciada",
        description=f"@{user.username} accedió al panel",
    ))
    await db.commit()

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    from jose import JWTError
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    from app.services.auth_service import get_user_by_id
    user = await get_user_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    access = create_access_token({"sub": str(user.id)})
    refresh_new = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access, refresh_token=refresh_new)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    balance = current_user.wallet.balance if current_user.wallet else 0.0
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        wallet_balance=balance,
    )
