"""
Traffic simulation engine — runs as a Celery beat periodic task.
Every 60s it simulates visits/conversions/revenue for each live asset,
creating the illusion of real traffic for the investor demo.
"""
import asyncio
import random
import logging
from datetime import datetime, date

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _simulate_tick_sync():
    """Synchronous wrapper — Celery tasks run in sync context."""
    asyncio.run(_simulate_tick_async())


async def _simulate_tick_async():
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.asset import Asset, AssetStatus
    from app.models.metrics import Metrics
    from app.models.activity import ActivityEvent, EventType

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Asset).where(Asset.status.in_(["live", "scaling", "optimizing"]))
        )
        assets = result.scalars().all()

        if not assets:
            return

        events_to_add = []

        for asset in assets:
            # Generate realistic but exciting traffic numbers
            base_visits = random.randint(3, 40)
            # Scale up assets get more traffic
            if asset.status.value == "scaling":
                base_visits = int(base_visits * random.uniform(1.5, 3.0))

            conversion_rate = random.uniform(0.01, 0.08)
            conversions = max(0, int(base_visits * conversion_rate))

            # Revenue depends on monetization model
            rev_per_conversion = {
                "affiliates": random.uniform(5.0, 45.0),
                "ads": random.uniform(0.1, 0.8) * base_visits,  # CPM-based
                "ecommerce": random.uniform(20.0, 150.0),
                "leads": random.uniform(3.0, 15.0),
                "none": 0.0,
            }
            model = asset.monetization_model.value if asset.monetization_model else "none"
            if model == "ads":
                revenue = rev_per_conversion[model]  # already visit-based
            else:
                revenue = conversions * rev_per_conversion.get(model, 0.0)

            revenue = round(revenue, 2)

            # Update asset totals
            asset.revenue = round((asset.revenue or 0.0) + revenue, 2)

            # Upsert today's metrics
            today = date.today()
            metric_result = await db.execute(
                select(Metrics).where(
                    Metrics.asset_id == asset.id,
                    Metrics.date == today,
                )
            )
            metric = metric_result.scalar_one_or_none()
            if metric:
                metric.visits += base_visits
                metric.conversions += conversions
                metric.revenue = round((metric.revenue or 0.0) + revenue, 2)
            else:
                metric = Metrics(
                    asset_id=asset.id,
                    date=today,
                    visits=base_visits,
                    conversions=conversions,
                    revenue=revenue,
                    bounce_rate=random.uniform(0.3, 0.75),
                    avg_session_duration=random.uniform(30, 180),
                )
                db.add(metric)

            # Emit activity event for significant revenue
            if revenue > 10:
                events_to_add.append(ActivityEvent(
                    asset_id=asset.id,
                    event_type=EventType.REVENUE_EARNED,
                    title=f"💰 €{revenue:.2f} generados",
                    description=f"{asset.keyword[:50]} — {base_visits} visitas, {conversions} conversiones",
                    data={"revenue": revenue, "visits": base_visits, "conversions": conversions},
                ))
            elif base_visits > 25:
                events_to_add.append(ActivityEvent(
                    asset_id=asset.id,
                    event_type=EventType.TRAFFIC_SPIKE,
                    title=f"📈 Spike de tráfico",
                    description=f"{asset.keyword[:50]} — {base_visits} visitas esta hora",
                    data={"visits": base_visits},
                ))

        for e in events_to_add:
            db.add(e)

        await db.commit()
        logger.info("Simulation tick: %d assets updated, %d events", len(assets), len(events_to_add))


@celery_app.task(name="app.workers.simulation.simulate_traffic_tick")
def simulate_traffic_tick():
    _simulate_tick_sync()
