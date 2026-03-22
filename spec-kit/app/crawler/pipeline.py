"""Crawl pipeline: dedup -> keyword filter -> score -> save -> FTS index."""
import json
import logging
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.crawler.dedup import is_duplicate
from app.crawler.keywords import extract_keywords
from app.crawler.scorer import calculate_score
from app.crawler.parsers.base import CrawledItem
from app.db.models import Article, Source

logger = logging.getLogger(__name__)


def process_item(db: Session, source: Source, item: CrawledItem) -> Article | None:
    if is_duplicate(db, item.url, item.title):
        return None

    keywords = extract_keywords(f"{item.title} {item.content}")
    if not keywords:
        return None

    score, breakdown = calculate_score(
        weight=source.weight,
        published_at=item.published_at,
        keyword_count=len(keywords),
        db=db,
    )

    article = Article(
        url=item.url,
        title=item.title,
        content=(item.content or "")[:2000],
        tags=json.dumps(keywords, ensure_ascii=False),
        source_id=source.id,
        category=source.category,
        score=score,
        score_breakdown=json.dumps(breakdown),
        published_at=item.published_at,
    )
    db.add(article)
    try:
        db.commit()
        db.refresh(article)
    except IntegrityError:
        db.rollback()
        return None

    try:
        db.execute(
            text("INSERT INTO article_fts(rowid, title, content) VALUES (:id, :title, :content)"),
            {"id": article.id, "title": article.title, "content": article.content or ""},
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("FTS insert failed for article %s: %s", article.id, exc)

    return article
