"""Crawl runner: orchestrates crawling all active sources."""
import logging
import threading
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import CrawlFailure, Source

logger = logging.getLogger(__name__)
_crawl_lock = threading.Lock()
_is_crawling = False


def get_crawl_status() -> bool:
    return _is_crawling


class CrawlRunner:
    def __init__(self, db: Session):
        self.db = db

    def run(self) -> dict:
        global _is_crawling
        if not _crawl_lock.acquire(blocking=False):
            return {"status": "already_running"}
        try:
            _is_crawling = True
            sources = self.db.query(Source).filter(Source.is_active.is_(True)).all()
            crawled = 0
            failed = 0
            for source in sources:
                try:
                    count = self._crawl_source(source)
                    crawled += count
                    source.last_crawled_at = datetime.now(timezone.utc)
                    source.last_error = None
                except Exception as e:
                    failed += 1
                    source.last_error = str(e)
                    self.db.add(CrawlFailure(
                        source_id=source.id,
                        error_message=str(e),
                        failed_at=datetime.now(timezone.utc),
                    ))
                    logger.error("Crawl failed for %s: %s", source.name, e)
            self.db.commit()
            return {"status": "done", "crawled": crawled, "failed": failed}
        finally:
            _is_crawling = False
            _crawl_lock.release()

    def _crawl_source(self, source: Source) -> int:
        # Placeholder: actual scraping logic would go here
        # For now, returns 0 (no items crawled)
        logger.info("Crawling source: %s (%s)", source.name, source.url)
        return 0
