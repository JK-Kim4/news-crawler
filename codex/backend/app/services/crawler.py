from datetime import UTC, datetime

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import Content
from app.models.crawl_job import CrawlJob
from app.models.enums import CrawlStatus
from app.models.source import Source
from app.services.summarizer import summarize_text


def _extract_article_body(entry: dict, selector: str) -> str:
    if "content" in entry and entry["content"]:
        value = entry["content"][0].get("value") or ""
        if value:
            return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    if "summary" in entry and entry["summary"]:
        return BeautifulSoup(entry["summary"], "html.parser").get_text(" ", strip=True)
    return selector


def ingest_source(db: Session, source: Source) -> int:
    if not source.rss_url:
        return 0

    parsed = feedparser.parse(source.rss_url)
    processed = 0
    for entry in parsed.get("entries", []):
        original_url = entry.get("link")
        if not original_url:
            continue
        existing = db.scalar(select(Content).where(Content.original_url == original_url))
        if existing:
            continue

        raw_content = _extract_article_body(entry, source.selector_content)
        summary, tags = summarize_text(entry.get("title", source.name), raw_content)
        published_at = None
        if entry.get("published"):
            published_at = date_parser.parse(entry["published"])

        content = Content(
            source_id=source.id,
            source_type=source.source_type,
            source_name=source.name,
            language=source.language,
            title=entry.get("title", "Untitled"),
            original_url=original_url,
            published_at=published_at,
            author=entry.get("author"),
            summary=summary,
            tags=tags,
            raw_content=raw_content,
        )
        db.add(content)
        processed += 1

    db.commit()
    return processed


def run_crawl(db: Session, source_ids: list[str] | None = None, trigger: str = "manual") -> CrawlJob:
    job = CrawlJob(trigger=trigger, status=CrawlStatus.RUNNING, started_at=datetime.now(UTC))
    db.add(job)
    db.commit()
    db.refresh(job)

    sources_stmt = select(Source).where(Source.is_active.is_(True))
    if source_ids:
        sources_stmt = sources_stmt.where(Source.id.in_(source_ids))
    sources = db.scalars(sources_stmt).all()

    total_processed = 0
    try:
        for source in sources:
            total_processed += ingest_source(db, source)
        job.status = CrawlStatus.SUCCESS
        job.items_processed = total_processed
        job.message = f"Processed {len(sources)} source(s)"
    except Exception as exc:  # pragma: no cover - defensive path
        job.status = CrawlStatus.FAILED
        job.message = str(exc)
        raise
    finally:
        job.finished_at = datetime.now(UTC)
        db.commit()
        db.refresh(job)
    return job

