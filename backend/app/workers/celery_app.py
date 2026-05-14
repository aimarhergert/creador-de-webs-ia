from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "aros",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks", "app.workers.simulation"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    beat_schedule={
        # Simulate traffic every 60 seconds for live demo feel
        "simulate-traffic-tick": {
            "task": "app.workers.simulation.simulate_traffic_tick",
            "schedule": 60.0,
        },
    },
)
