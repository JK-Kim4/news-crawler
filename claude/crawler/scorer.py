from datetime import datetime, timezone


def calculate_score(
    weight: int,
    published_at: datetime | None,
    keyword_count: int,
) -> tuple[int, dict]:
    """
    Calculate a composite score for a news article.

    Args:
        weight: Source weight (1-10)
        published_at: Publication datetime (naive assumed UTC, or timezone-aware)
        keyword_count: Number of relevant keywords found

    Returns:
        Tuple of (total_score, breakdown_dict) where breakdown contains:
        - source: source score (0-50)
        - recency: recency score (0-30)
        - keyword: keyword score (0-20)
        - total: sum of all scores
    """

    # Calculate source score: clamp(weight, 1, 10) × 5 → max 50
    clamped_weight = max(1, min(10, weight))
    source_score = clamped_weight * 5

    # Calculate recency score
    recency_score = _calculate_recency_score(published_at)

    # Calculate keyword score: min(keyword_count × 2, 20) → max 20
    keyword_score = min(keyword_count * 2, 20)

    total_score = source_score + recency_score + keyword_score

    breakdown = {
        "source": source_score,
        "recency": recency_score,
        "keyword": keyword_score,
        "total": total_score,
    }

    return total_score, breakdown


def _calculate_recency_score(published_at: datetime | None) -> int:
    """
    Calculate recency score based on time since publication.

    Tiers:
    - Within 24 hours: 30
    - Within 48 hours: 20
    - Within 7 days: 10
    - Older or None: 5
    """
    if published_at is None:
        return 5

    # Handle naive datetime by assuming UTC
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    age = now - published_at

    # Check tiers
    if age.total_seconds() <= 24 * 3600:  # 24시간 이내
        return 30
    elif age.total_seconds() <= 48 * 3600:  # 48시간 이내
        return 20
    elif age.total_seconds() <= 7 * 24 * 3600:  # 7일 이내
        return 10
    else:
        return 5
