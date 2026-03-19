import json
import logging
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from crawler.keywords import extract_keywords
from crawler.scorer import calculate_score
from crawler.sources.base import CrawledItem
from db.models import Article, Source

logger = logging.getLogger(__name__)


def process_item(db: Session, source: Source, item: CrawledItem) -> Article | None:
    """
    단일 CrawledItem을 처리한다.
    - 중복 URL → None 반환
    - AI 키워드 미포함 → None 반환
    - 통과 → Article 저장 후 반환
    """
    # 중복 체크
    existing = db.query(Article).filter_by(url=item.url).first()
    if existing:
        return None

    # 키워드 필터링 + 태깅 (동일 키워드 목록으로 동시 처리)
    combined = f"{item.title} {item.content}"
    keywords = extract_keywords(combined)
    if not keywords:
        return None

    # 스코어 계산
    score, breakdown = calculate_score(
        weight=source.weight,
        published_at=item.published_at,
        keyword_count=len(keywords),
    )

    article = Article(
        url=item.url,
        title=item.title,
        content=item.content[:2000],  # 최대 2000자
        tags=json.dumps(keywords, ensure_ascii=False),
        source_id=source.id,
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
            {
                "id": article.id,
                "title": article.title,
                "content": article.content or "",
            },
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("FTS insert failed for article %s: %s", article.id, exc)

    return article
