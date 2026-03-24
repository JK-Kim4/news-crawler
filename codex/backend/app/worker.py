from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings


settings = get_settings()
celery_app = Celery("ai_insights", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.beat_schedule = {
    "crawl-every-six-hours": {
        "task": "app.worker.run_scheduled_crawl",
        "schedule": crontab(minute=0, hour="*/6"),
    }
}


@celery_app.task(name="app.worker.run_scheduled_crawl")
def run_scheduled_crawl():
    from app.tasks.crawl import trigger_manual_crawl

    return trigger_manual_crawl([], "scheduled")

