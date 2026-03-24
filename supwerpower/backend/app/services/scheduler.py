import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _run_crawl_job():
    from app.services.crawler import scheduled_crawl

    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.ensure_future(scheduled_crawl())
    else:
        loop.run_until_complete(scheduled_crawl())


def init_scheduler():
    scheduler.add_job(
        _run_crawl_job,
        trigger=IntervalTrigger(hours=settings.CRAWL_INTERVAL_HOURS),
        id="crawl_job",
        name="Periodic news crawl",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"Scheduler started with {settings.CRAWL_INTERVAL_HOURS}-hour crawl interval"
    )


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")


def get_next_run_time() -> str | None:
    job = scheduler.get_job("crawl_job")
    if job and job.next_run_time:
        return job.next_run_time.isoformat()
    return None
