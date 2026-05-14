"""
Seed script — idempotent demo data for AROS investor demo.

Usage (inside Docker):
  docker compose exec backend python -m scripts.seed

Creates:
- 6 preset strategies
- Subscription (Professional) for demo users
- Projects grouped by strategy
- TrafficSimulation records for live assets
- OptimizationLog history for completed decisions
- Demo investments
"""
import asyncio
import random
import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import (
    Base, User, Wallet, Asset, AssetStatus,
    Strategy, StrategyType, STRATEGY_PRESETS,
    Project, ProjectStatus,
    Subscription, SubscriptionPlan, SubscriptionStatus, PLAN_CONFIG,
    OptimizationLog, OptimizationDecision,
    TrafficSimulation,
    Investment, InvestmentStatus,
    ActivityEvent, EventType,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("seed")

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_or_create_strategies(db: AsyncSession) -> list[Strategy]:
    """Seed 6 preset strategies, skipping existing ones."""
    existing = (await db.execute(select(Strategy).where(Strategy.is_preset == True))).scalars().all()
    existing_types = {s.type for s in existing}

    name_map = {
        "seo_growth":          "SEO Growth",
        "affiliate_arbitrage": "Affiliate Arbitrage",
        "lead_generation":     "Lead Generation",
        "micro_saas":          "Micro SaaS",
        "aggressive_scaling":  "Aggressive Scaling",
        "conservative_roi":    "Conservative ROI",
    }

    created = []
    for strat_type, params in STRATEGY_PRESETS.items():
        if StrategyType(strat_type) in existing_types:
            continue
        s = Strategy(
            name=name_map[strat_type],
            type=StrategyType(strat_type),
            is_preset=True,
            **params,
        )
        db.add(s)
        created.append(s)
        log.info(f"  + Strategy: {name_map[strat_type]}")

    await db.flush()
    all_strategies = (await db.execute(select(Strategy).where(Strategy.is_preset == True))).scalars().all()
    return all_strategies


async def _seed_subscription(db: AsyncSession, user: User) -> None:
    """Upsert a Professional subscription for demo users."""
    existing = (await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )).scalar_one_or_none()

    if existing:
        log.info(f"  ~ Subscription already exists for {user.username}")
        return

    cfg = PLAN_CONFIG["professional"]
    sub = Subscription(
        user_id=user.id,
        plan=SubscriptionPlan.PROFESSIONAL,
        status=SubscriptionStatus.ACTIVE,
        assets_limit=cfg["assets"],
        strategies_limit=cfg["strategies"],
        current_period_start=datetime.utcnow() - timedelta(days=15),
        current_period_end=datetime.utcnow() + timedelta(days=15),
    )
    db.add(sub)
    log.info(f"  + Subscription (Professional) for {user.username}")


async def _seed_projects(
    db: AsyncSession, user: User, strategies: list[Strategy], assets: list[Asset]
) -> list[Project]:
    """Create demo projects if user has none."""
    existing = (await db.execute(
        select(Project).where(Project.user_id == user.id)
    )).scalars().all()
    if existing:
        log.info(f"  ~ Projects already exist for {user.username}")
        return existing

    strategy_map = {s.type: s for s in strategies}
    projects_data = [
        ("Proyecto Afiliados Premium", StrategyType.AFFILIATE_ARBITRAGE, 800.0),
        ("SEO Orgánico Q2", StrategyType.SEO_GROWTH, 400.0),
        ("Lead Gen B2B", StrategyType.LEAD_GENERATION, 600.0),
    ]

    created = []
    for name, strat_type, budget in projects_data:
        strat = strategy_map.get(strat_type)
        p = Project(
            user_id=user.id,
            strategy_id=strat.id if strat else None,
            name=name,
            status=ProjectStatus.ACTIVE,
            total_budget=budget,
            spent_budget=round(budget * random.uniform(0.4, 0.8), 2),
            created_at=datetime.utcnow() - timedelta(days=random.randint(20, 60)),
        )
        db.add(p)
        created.append(p)
        log.info(f"  + Project: {name}")

    await db.flush()
    return created


async def _seed_traffic_simulations(db: AsyncSession, assets: list[Asset], strategies: list[Strategy]) -> None:
    """Create TrafficSimulation records for live/scaling/optimizing assets."""
    strategy_map = {s.type: s for s in strategies}
    active_statuses = {AssetStatus.LIVE, AssetStatus.SCALING, AssetStatus.OPTIMIZING}

    for asset in assets:
        if asset.status not in active_statuses:
            continue

        existing = (await db.execute(
            select(TrafficSimulation).where(TrafficSimulation.asset_id == asset.id)
        )).scalar_one_or_none()
        if existing:
            continue

        strat = strategy_map.get(StrategyType.AFFILIATE_ARBITRAGE)
        base_visits = strat.visits_min + random.randint(0, strat.visits_max - strat.visits_min) if strat else 15
        conv_rate = random.uniform(0.03, 0.08)
        rev_per_conv = random.uniform(15.0, 80.0)

        multiplier = 1.5 if asset.status == AssetStatus.SCALING else 1.0
        sim = TrafficSimulation(
            asset_id=asset.id,
            base_visits_per_tick=int(base_visits * multiplier),
            conversion_rate=conv_rate,
            revenue_per_conversion=rev_per_conv,
            growth_rate=random.uniform(0.02, 0.08),
            volatility=random.uniform(0.15, 0.35),
            total_visits=random.randint(500, 8000),
            total_conversions=random.randint(20, 400),
            total_revenue=round(asset.revenue, 2),
            is_active=True,
            tick_count=random.randint(50, 300),
            last_tick_at=datetime.utcnow() - timedelta(seconds=random.randint(30, 120)),
        )
        db.add(sim)
        log.info(f"  + TrafficSimulation for asset #{asset.id} ({asset.keyword[:40]})")


async def _seed_optimization_logs(
    db: AsyncSession, assets: list[Asset], strategies: list[Strategy]
) -> None:
    """Create historical optimization decisions for demo assets."""
    strategy_map = {s.type: s for s in strategies}
    strat = strategy_map.get(StrategyType.AFFILIATE_ARBITRAGE)

    decision_scenarios = [
        (AssetStatus.SCALING,   OptimizationDecision.SCALE,    4.2,  "ROI 4.2 > 3.0 → ESCALAR. Duplicando presupuesto."),
        (AssetStatus.OPTIMIZING,OptimizationDecision.OPTIMIZE, 1.8,  "ROI 1.8 dentro de umbral → OPTIMIZAR landing page."),
        (AssetStatus.KILLED,    OptimizationDecision.KILL,     0.6,  "ROI 0.6 < 1.0 tras 14 días → ELIMINAR. Reasignando capital."),
        (AssetStatus.LIVE,      OptimizationDecision.HOLD,     2.1,  "ROI 2.1 estable. Manteniendo configuración actual."),
    ]

    assets_by_status = {s: [a for a in assets if a.status == s] for s, *_ in decision_scenarios}

    for status, decision, roi, reasoning in decision_scenarios:
        targets = assets_by_status.get(status, [])[:2]
        for asset in targets:
            existing = (await db.execute(
                select(OptimizationLog).where(
                    OptimizationLog.asset_id == asset.id,
                    OptimizationLog.decision == decision,
                )
            )).scalar_one_or_none()
            if existing:
                continue

            capital_before = round(random.uniform(100, 500), 2)
            capital_delta = capital_before * 1.5 if decision == OptimizationDecision.SCALE else capital_before
            log_entry = OptimizationLog(
                asset_id=asset.id,
                strategy_id=strat.id if strat else None,
                decision=decision,
                roi_at_decision=roi + random.uniform(-0.2, 0.2),
                revenue_at_decision=round(asset.revenue * random.uniform(0.3, 0.8), 2),
                cost_at_decision=round(asset.cost, 2),
                days_tracked=random.randint(7, 21),
                capital_before=capital_before,
                capital_after=round(capital_delta, 2),
                reasoning=reasoning,
                executed=True,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 10)),
            )
            db.add(log_entry)
            log.info(f"  + OptimizationLog: {decision.value.upper()} for asset #{asset.id}")


async def _seed_investments(db: AsyncSession, user: User, assets: list[Asset], strategies: list[Strategy]) -> None:
    """Create demo investment allocations."""
    wallet = user.wallet
    if not wallet:
        return

    existing = (await db.execute(
        select(Investment).where(Investment.wallet_id == wallet.id)
    )).scalars().all()
    if existing:
        log.info(f"  ~ Investments already exist for {user.username}")
        return

    strategy_map = {s.type: s for s in strategies}
    live_assets = [a for a in assets if a.status in (AssetStatus.LIVE, AssetStatus.SCALING)][:5]

    for asset in live_assets:
        amount = round(random.uniform(50, 200), 2)
        returned = round(amount * random.uniform(1.0, 3.5), 2)
        strat = strategy_map.get(StrategyType.AFFILIATE_ARBITRAGE)
        inv = Investment(
            wallet_id=wallet.id,
            asset_id=asset.id,
            strategy_id=strat.id if strat else None,
            amount=amount,
            returned_amount=returned,
            status=InvestmentStatus.ACTIVE if asset.status != AssetStatus.KILLED else InvestmentStatus.RETURNED,
            allocated_at=datetime.utcnow() - timedelta(days=random.randint(5, 30)),
        )
        db.add(inv)
        log.info(f"  + Investment €{amount} → asset #{asset.id}")


# ── Main ─────────────────────────────────────────────────────────────────────

async def seed():
    async with Session() as db:
        log.info("=== AROS Seed Script ===")

        # 1. Strategies
        log.info("\n[1/5] Seeding strategies…")
        strategies = await _get_or_create_strategies(db)
        await db.commit()

        # 2. Load demo users
        result = await db.execute(select(User))
        users = result.scalars().all()
        if not users:
            log.warning("No users found — run the app first so create_all creates the tables and register users.")
            return

        log.info(f"\n[2/5] Seeding subscriptions for {len(users)} user(s)…")
        for user in users:
            await _seed_subscription(db, user)
        await db.commit()

        # 3. Load all assets
        result = await db.execute(select(Asset))
        assets = result.scalars().all()
        log.info(f"  Found {len(assets)} asset(s)")

        # 4. Traffic simulations
        log.info("\n[3/5] Seeding traffic simulations…")
        await _seed_traffic_simulations(db, assets, strategies)
        await db.commit()

        # 5. Optimization logs
        log.info("\n[4/5] Seeding optimization logs…")
        await _seed_optimization_logs(db, assets, strategies)
        await db.commit()

        # 6. Projects + Investments per user
        log.info("\n[5/5] Seeding projects & investments…")
        for user in users:
            await _seed_projects(db, user, strategies, assets)
            await _seed_investments(db, user, assets, strategies)
        await db.commit()

        log.info("\n✓ Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
