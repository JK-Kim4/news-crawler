import logging
import threading
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from crawler.loader import load_and_sync_sources
from crawler.pipeline import process_item
from crawler.sources.rss import RssCrawler
from crawler.sources.scraper import ScraperCrawler
from db.models import CrawlFailure, Source

logger = logging.getLogger(__name__)

_is_crawling = False
_lock = threading.Lock()


def get_crawl_status() -> bool:
    """Return whether a crawl is currently running."""
    with _lock:
        return _is_crawling


class CrawlRunner:
    def __init__(self, db: Session, config_path: str = "config/sources.json"):
        self.db = db
        self.config_path = config_path

    def run(self) -> dict:
        """전체 크롤링 실행. 이미 실행 중이면 즉시 반환."""
        global _is_crawling
        with _lock:
            if _is_crawling:
                return {"status": "already_running"}
            _is_crawling = True

        try:
            load_and_sync_sources(self.db, self.config_path)
            crawled, failed = 0, 0

            # 재시도 먼저
            for failure in self._get_retryable_failures():
                success = self._retry_failure(failure)
                if success:
                    crawled += 1
                else:
                    failed += 1

            # 정상 크롤링
            sources = self.db.query(Source).filter_by(is_active=True).all()
            for source in sources:
                c, f = self._crawl_source(source)
                crawled += c
                failed += f

            return {"status": "done", "crawled": crawled, "failed": failed}
        finally:
            with _lock:
                _is_crawling = False

    def _crawl_source(self, source: Source) -> tuple[int, int]:
        crawled, failed = 0, 0
        try:
            crawler = RssCrawler(source.url) if source.type == "rss" else ScraperCrawler(source.url)
            items = crawler.fetch()
            for item in items:
                try:
                    result = process_item(self.db, source, item)
                    if result:
                        crawled += 1
                except Exception as e:
                    self._record_failure(source, item.url, str(e))
                    failed += 1
            # 소스 fetch는 성공했으므로 last_crawled_at 갱신.
            # 개별 기사 처리 실패는 CrawlFailure에 별도 기록되므로 last_error는 None 처리.
            source.last_crawled_at = datetime.now(timezone.utc)
            source.last_error = None
            self.db.commit()
        except Exception as e:
            logger.error(f"Source {source.name} failed: {e}")
            source.last_error = str(e)
            self.db.commit()
            self._record_failure(source, None, str(e))
            failed += 1
        return crawled, failed

    def _record_failure(self, source: Source, url: str | None, error: str) -> None:
        failure = CrawlFailure(
            source_id=source.id,
            url=url,
            error_message=error,
            failed_at=datetime.now(timezone.utc),
        )
        self.db.add(failure)
        self.db.commit()

    def _get_retryable_failures(self) -> list[CrawlFailure]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
        return (
            self.db.query(CrawlFailure)
            .filter(
                CrawlFailure.resolved_at.is_(None),
                CrawlFailure.retry_count < 3,
                CrawlFailure.failed_at < cutoff,
            )
            .all()
        )

    def _retry_failure(self, failure: CrawlFailure) -> bool:
        source = self.db.get(Source, failure.source_id)
        if not source:
            return False
        try:
            crawler = RssCrawler(source.url) if source.type == "rss" else ScraperCrawler(source.url)
            items = crawler.fetch()

            if failure.url:
                # 특정 URL 실패 재시도: 피드에서 해당 URL을 찾아 처리
                matched = False
                for item in items:
                    if item.url == failure.url:
                        process_item(self.db, source, item)
                        matched = True
                        break
                if not matched:
                    # 피드에서 URL이 사라진 경우 — 더 이상 재시도 불필요, resolved 처리
                    logger.info("Failure URL no longer in feed, marking resolved: %s", failure.url)
            else:
                # 소스 전체 실패 재시도: 모든 기사 처리
                for item in items:
                    process_item(self.db, source, item)

            failure.resolved_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        except Exception as e:
            failure.retry_count += 1
            failure.failed_at = datetime.now(timezone.utc)
            failure.error_message = str(e)
            self.db.commit()
            return False
