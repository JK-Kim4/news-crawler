"""Rule-based article scoring with DB-configurable weights."""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_DEFAULT_WEIGHTS = {
    "source_trust": 1.0,
    "recency": 1.0,
    "keyword": 1.0,
    "engagement": 0.5,
}


def _load_weights(db: Session | None) -> dict[str, float]:
    if db is None:
        return _DEFAULT_WEIGHTS.copy()
    try:
        from app.db.models import ScoringWeight
        rows = db.query(ScoringWeight).all()
        if rows:
            return {r.key: r.weight for r in rows}
    except Exception as e:
        logger.warning("Failed to load scoring weights: %s", e)
    return _DEFAULT_WEIGHTS.copy()


def calculate_score(
    weight: float,
    published_at: datetime | None,
    keyword_count: int,
    like_count: int = 0,
    db: Session | None = None,
) -> tuple[int, dict]:
    w = _load_weights(db)
    source_score = max(1, min(10, weight)) * 5 * w.get("source_trust", 1.0)
    recency_score = _recency_score(published_at) * w.get("recency", 1.0)
    keyword_score = min(keyword_count * 2, 20) * w.get("keyword", 1.0)
    engagement_score = min(like_count * 2, 10) * w.get("engagement", 0.5)
    total = int(source_score + recency_score + keyword_score + engagement_score)
    breakdown = {
        "source": round(source_score, 1),
        "recency": round(recency_score, 1),
        "keyword": round(keyword_score, 1),
        "engagement": round(engagement_score, 1),
        "total": total,
    }
    return total, breakdown


def _recency_score(published_at: datetime | None) -> int:
    if published_at is None:
        return 5
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - published_at).total_seconds()
    if age <= 86400:
        return 30
    if age <= 172800:
        return 20
    if age <= 604800:
        return 10
    return 5
