from datetime import datetime, timedelta, timezone
from crawler.scorer import calculate_score

def _now():
    return datetime.now(timezone.utc)

def test_score_max():
    score, breakdown = calculate_score(
        weight=10,
        published_at=_now() - timedelta(hours=1),
        keyword_count=10,
    )
    assert score == 100
    assert breakdown["source"] == 50
    assert breakdown["recency"] == 30
    assert breakdown["keyword"] == 20

def test_score_recency_tiers():
    _, b1 = calculate_score(10, _now() - timedelta(hours=12), 0)
    _, b2 = calculate_score(10, _now() - timedelta(hours=36), 0)
    _, b3 = calculate_score(10, _now() - timedelta(days=5), 0)
    _, b4 = calculate_score(10, _now() - timedelta(days=10), 0)
    assert b1["recency"] == 30
    assert b2["recency"] == 20
    assert b3["recency"] == 10
    assert b4["recency"] == 5

def test_score_keyword_capped_at_20():
    _, breakdown = calculate_score(5, _now(), keyword_count=15)
    assert breakdown["keyword"] == 20

def test_score_min_weight():
    score, breakdown = calculate_score(1, _now() - timedelta(days=10), 0)
    assert breakdown["source"] == 5
    assert score == 10  # 5 + 5 + 0

def test_score_no_published_at():
    score, breakdown = calculate_score(5, None, 3)
    assert breakdown["recency"] == 5
    assert breakdown["keyword"] == 6
