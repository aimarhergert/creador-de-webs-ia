import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.workers.celery_app import celery_app
from app.config import settings
from app.schemas.orchestrator import PipelineRequest
from app.models.asset import AssetType, MonetizationModel

logger = logging.getLogger(__name__)

_worker_engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
_WorkerSession = async_sessionmaker(_worker_engine, expire_on_commit=False, class_=AsyncSession)


def _run(coro):
    """Run async coroutine from a Celery sync task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@celery_app.task(bind=True, name="tasks.run_pipeline", max_retries=2)
def run_pipeline_task(self, keyword: str, asset_type: str, monetization: str):
    logger.info(f"[Task] Pipeline iniciado — keyword='{keyword}' task={self.request.id}")

    # Phase 0 progress
    self.update_state(
        state="PROGRESS",
        meta={"step": "market", "pct": 5, "msg": "Analizando mercado y planificando sitio…"},
    )

    async def _execute():
        from app.orchestrator import run_pipeline

        request = PipelineRequest(
            keyword=keyword,
            type=AssetType(asset_type),
            monetization_model=MonetizationModel(monetization),
        )
        async with _WorkerSession() as db:
            asset = await run_pipeline(request, db)
            return {
                "asset_id": asset.id,
                "url":      asset.url,
                "status":   asset.status.value,
                "keyword":  asset.keyword,
            }

    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "generating", "pct": 15, "msg": "Generando sitio premium con IA (8 archivos)…"},
        )
        result = _run(_execute())
        logger.info(f"[Task] Pipeline completado — asset #{result['asset_id']} en {result['url']}")
        return result

    except Exception as exc:
        logger.error(f"[Task] Fallo en pipeline '{keyword}': {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.optimize_portfolio")
def optimize_portfolio_task():
    logger.info("[Task] Iniciando optimización de portfolio")

    async def _execute():
        from app.services.optimization_engine import run_portfolio_optimization
        async with _WorkerSession() as db:
            return await run_portfolio_optimization(db)

    return _run(_execute())
