import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "sentineliq_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def generate_async_report(report_id: str, report_type: str):
    # This background task represents a production worker compiling heavy statistics
    # and caching forecasts.
    print(f"Background task: Compiling {report_type} report for id {report_id}...")
    # In production, this would do heavy database aggregates and write back to report payload
    return {"status": "success", "report_id": report_id}
