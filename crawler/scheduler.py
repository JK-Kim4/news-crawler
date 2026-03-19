import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler(crawl_fn):
    """크롤링 함수를 6시간마다 실행하는 백그라운드 스케줄러를 시작한다."""
    global _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        crawl_fn,
        trigger=IntervalTrigger(hours=6),
        id="crawl_job",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started: crawl every 6 hours")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
