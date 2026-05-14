from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction, TransactionType
from app.models.activity import ActivityEvent, EventType

router = APIRouter()


class DepositRequest(BaseModel):
    amount: float
    description: str | None = None


class WalletOut(BaseModel):
    id: int
    balance: float
    total_deposited: float
    total_invested: float
    total_returned: float
    currency: str
    roi: float
    pnl: float

    model_config = {"from_attributes": True}


class TransactionOut(BaseModel):
    id: int
    type: str
    amount: float
    balance_after: float
    description: str | None
    asset_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


async def _get_or_create_wallet(db: AsyncSession, user_id: int) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0.0)
        db.add(wallet)
        await db.flush()
    return wallet


@router.get("", response_model=WalletOut)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wallet = await _get_or_create_wallet(db, current_user.id)
    await db.commit()
    return WalletOut(
        id=wallet.id,
        balance=wallet.balance,
        total_deposited=wallet.total_deposited,
        total_invested=wallet.total_invested,
        total_returned=wallet.total_returned,
        currency=wallet.currency,
        roi=wallet.roi,
        pnl=wallet.pnl,
    )


@router.post("/deposit", response_model=WalletOut)
async def deposit(
    body: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="El importe debe ser positivo")
    if body.amount > 100_000:
        raise HTTPException(status_code=400, detail="Máximo €100,000 por depósito (demo)")

    wallet = await _get_or_create_wallet(db, current_user.id)
    wallet.balance += body.amount
    wallet.total_deposited += body.amount

    tx = WalletTransaction(
        wallet_id=wallet.id,
        type=TransactionType.DEPOSIT,
        amount=body.amount,
        balance_after=wallet.balance,
        description=body.description or f"Depósito de €{body.amount:,.2f}",
    )
    db.add(tx)

    db.add(ActivityEvent(
        user_id=current_user.id,
        event_type=EventType.WALLET_DEPOSIT,
        title=f"Depósito de €{body.amount:,.2f}",
        description=f"Saldo nuevo: €{wallet.balance:,.2f}",
        data={"amount": body.amount, "balance": wallet.balance},
    ))

    await db.commit()
    return WalletOut(
        id=wallet.id, balance=wallet.balance, total_deposited=wallet.total_deposited,
        total_invested=wallet.total_invested, total_returned=wallet.total_returned,
        currency=wallet.currency, roi=wallet.roi, pnl=wallet.pnl,
    )


@router.get("/transactions", response_model=list[TransactionOut])
async def get_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wallet = await _get_or_create_wallet(db, current_user.id)
    await db.commit()
    txs = wallet.transactions[:limit]
    return [
        TransactionOut(
            id=t.id, type=t.type.value, amount=t.amount,
            balance_after=t.balance_after, description=t.description,
            asset_id=t.asset_id, created_at=t.created_at,
        )
        for t in txs
    ]
