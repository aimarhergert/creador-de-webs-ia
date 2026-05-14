from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_user
from app.models.investment import Investment, InvestmentStatus
from app.models.wallet import Wallet, WalletTransaction, TransactionType
from app.models.user import User
from app.schemas.investment import (
    InvestmentCreate, InvestmentOut, InvestmentListOut, InvestmentSummary,
)

router = APIRouter()


@router.get("", response_model=InvestmentListOut)
async def list_investments(
    status: InvestmentStatus | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = current_user.wallet
    if not wallet:
        return InvestmentListOut(total=0, items=[])

    query = select(Investment).where(Investment.wallet_id == wallet.id)
    if status:
        query = query.where(Investment.status == status)

    count = await db.execute(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset(offset).limit(limit).order_by(Investment.created_at.desc()))
    return InvestmentListOut(total=count.scalar(), items=result.scalars().all())


@router.get("/summary", response_model=InvestmentSummary)
async def get_investment_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = current_user.wallet
    if not wallet:
        return InvestmentSummary(
            total_invested=0, total_returned=0, active_count=0, total_count=0,
            portfolio_roi=0.0, portfolio_pnl=0.0, by_strategy={},
        )

    result = await db.execute(
        select(Investment).where(Investment.wallet_id == wallet.id)
    )
    investments = result.scalars().all()

    total_invested = sum(i.amount for i in investments)
    total_returned = sum(i.returned_amount for i in investments)
    active_count = sum(1 for i in investments if i.status == InvestmentStatus.ACTIVE)

    # Group by strategy_id
    by_strategy: dict[str, float] = {}
    for inv in investments:
        key = str(inv.strategy_id) if inv.strategy_id else "sin_estrategia"
        by_strategy[key] = by_strategy.get(key, 0.0) + inv.amount

    return InvestmentSummary(
        total_invested=round(total_invested, 2),
        total_returned=round(total_returned, 2),
        active_count=active_count,
        total_count=len(investments),
        portfolio_roi=round(total_returned / total_invested, 2) if total_invested > 0 else 0.0,
        portfolio_pnl=round(total_returned - total_invested, 2),
        by_strategy=by_strategy,
    )


@router.get("/{investment_id}", response_model=InvestmentOut)
async def get_investment(
    investment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = current_user.wallet
    result = await db.execute(
        select(Investment).where(
            Investment.id == investment_id,
            Investment.wallet_id == wallet.id,
        )
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Inversión no encontrada")
    return inv


@router.post("", response_model=InvestmentOut, status_code=201)
async def create_investment(
    body: InvestmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = current_user.wallet
    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet no encontrada")
    if wallet.balance < body.amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")

    # Deduct from wallet
    wallet.balance = round(wallet.balance - body.amount, 2)
    wallet.total_invested = round(wallet.total_invested + body.amount, 2)

    tx = WalletTransaction(
        wallet_id=wallet.id,
        type=TransactionType.ALLOCATION,
        amount=-body.amount,
        balance_after=wallet.balance,
        description=f"Inversión asignada — asset #{body.asset_id or '?'}",
        asset_id=body.asset_id,
    )
    db.add(tx)

    inv = Investment(
        wallet_id=wallet.id,
        asset_id=body.asset_id,
        strategy_id=body.strategy_id,
        project_id=body.project_id,
        amount=body.amount,
        status=InvestmentStatus.ACTIVE,
        notes=body.notes,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    return inv
