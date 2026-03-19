from datetime import datetime, timedelta, timezone
from crawler.runner import CrawlRunner
from db.models import Source, CrawlFailure

def _make_source(db, source_type="rss"):
    source = Source(name="Test", url="https://test.com/feed", type=source_type, weight=7)
    db.add(source)
    db.commit()
    return source

def test_retry_skips_resolved_failures(db):
    source = _make_source(db)
    failure = CrawlFailure(
        source_id=source.id,
        url="https://test.com/1",
        error_message="timeout",
        failed_at=datetime.now(timezone.utc) - timedelta(hours=12),
        retry_count=1,
        resolved_at=datetime.now(timezone.utc),  # already resolved
    )
    db.add(failure)
    db.commit()
    runner = CrawlRunner(db, config_path="config/sources.json")
    retried = runner._get_retryable_failures()
    assert len(retried) == 0

def test_retry_skips_exceeded_count(db):
    source = _make_source(db)
    failure = CrawlFailure(
        source_id=source.id,
        url="https://test.com/1",
        error_message="timeout",
        failed_at=datetime.now(timezone.utc) - timedelta(hours=12),
        retry_count=3,  # at limit
    )
    db.add(failure)
    db.commit()
    runner = CrawlRunner(db, config_path="config/sources.json")
    retried = runner._get_retryable_failures()
    assert len(retried) == 0

def test_retry_skips_too_recent(db):
    source = _make_source(db)
    failure = CrawlFailure(
        source_id=source.id,
        url="https://test.com/1",
        error_message="timeout",
        failed_at=datetime.now(timezone.utc) - timedelta(hours=3),  # < 6h ago
        retry_count=1,
    )
    db.add(failure)
    db.commit()
    runner = CrawlRunner(db, config_path="config/sources.json")
    retried = runner._get_retryable_failures()
    assert len(retried) == 0

def test_retry_includes_eligible(db):
    source = _make_source(db)
    failure = CrawlFailure(
        source_id=source.id,
        url="https://test.com/1",
        error_message="timeout",
        failed_at=datetime.now(timezone.utc) - timedelta(hours=8),  # > 6h ago
        retry_count=1,
    )
    db.add(failure)
    db.commit()
    runner = CrawlRunner(db, config_path="config/sources.json")
    retried = runner._get_retryable_failures()
    assert len(retried) == 1
