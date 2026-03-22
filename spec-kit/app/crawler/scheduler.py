"""APScheduler integration for periodic crawling."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def start_scheduler(crawl_func, interval_hours: int = 6):
    global _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(crawl_func, "interval", hours=interval_hours, id="crawl_job")
    _scheduler.start()
    logger.info("Scheduler started: crawl every %d hours", interval_hours)


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
