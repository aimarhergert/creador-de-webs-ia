import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.orchestrator import run_pipeline
from app.schemas.orchestrator import PipelineRequest, PipelineResponse
from app.services.optimization_engine import run_portfolio_optimization, evaluate_asset

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/pipeline", response_model=PipelineResponse, status_code=202)
async def trigger_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Full autonomous pipeline: market → AI generation → deploy → monetize.
    async_mode=true  → queues Celery task, returns task_id immediately.
    async_mode=false → runs synchronously (blocks until done, ~30s).
    """
    if request.async_mode:
        try:
            from app.workers.tasks import run_pipeline_task
            task = run_pipeline_task.delay(
                request.keyword,
                request.type.value,
                request.monetization_model.value,
            )
            logger.info(f"[Route] Pipeline encolado — task_id={task.id}")
            return PipelineResponse(
                task_id=task.id,
                status="queued",
                message=f"Pipeline encolado. Sigue el progreso en /api/orchestrate/tasks/{task.id}",
            )
        except Exception as exc:
            logger.warning(f"[Route] Celery no disponible, fallback síncrono: {exc}")

    # Sync fallback (or async_mode=false)
    asset = await run_pipeline(request, db)
    return PipelineResponse(
        asset_id=asset.id,
        status=asset.status.value,
        message=f"Pipeline completado. Asset en: {asset.url}",
    )


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Poll Celery task status.
    States: queued → running → done / error
    """
    try:
        from app.workers.celery_app import celery_app
        from celery.result import AsyncResult

        task = AsyncResult(task_id, app=celery_app)
        state = task.state

        if state == "PENDING":
            return {"status": "queued",   "pct": 0,   "msg": "En cola…"}
        if state == "STARTED":
            return {"status": "running",  "pct": 10,  "msg": "Iniciando pipeline…"}
        if state == "PROGRESS":
            meta = task.info or {}
            return {
                "status": "running",
                "pct":    meta.get("pct", 30),
                "msg":    meta.get("msg", "Procesando…"),
                "step":   meta.get("step", ""),
            }
        if state == "SUCCESS":
            result = task.result or {}
            return {
                "status":   "done",
                "pct":      100,
                "asset_id": result.get("asset_id"),
                "url":      result.get("url"),
                "result":   result,
            }
        # FAILURE / REVOKED / unknown
        err = str(task.result) if task.result else "Error desconocido"
        return {"status": "error", "pct": 0, "msg": err}

    except Exception as exc:
        logger.error(f"[Route] Error leyendo estado de tarea {task_id}: {exc}")
        return {"status": "error", "pct": 0, "msg": str(exc)}


@router.post("/optimize", status_code=200)
async def optimize_portfolio(db: AsyncSession = Depends(get_db)):
    """Run ROI-based optimization on all live assets."""
    results = await run_portfolio_optimization(db)
    return {"evaluated": len(results), "results": results}


@router.post("/optimize/{asset_id}", status_code=200)
async def optimize_single_asset(asset_id: int, db: AsyncSession = Depends(get_db)):
    return await evaluate_asset(db, asset_id)
