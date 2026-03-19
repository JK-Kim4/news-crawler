from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from db.models import Article, Source, CrawlFailure, UserNote


def test_source_creation(db):
    source = Source(name="Test Blog", url="https://test.com/feed", type="rss", weight=7)
    db.add(source)
    db.commit()
    assert source.id is not None
    assert source.is_active is True
    assert source.crawl_interval_hours == 6


def test_article_url_unique(db):
    source = Source(name="Test", url="https://test.com/feed", type="rss", weight=5)
    db.add(source)
    db.commit()
    a1 = Article(url="https://test.com/article/1", title="T1", source_id=source.id,
                 score=50, score_breakdown="{}", tags="[]")
    a2 = Article(url="https://test.com/article/1", title="T2", source_id=source.id,
                 score=50, score_breakdown="{}", tags="[]")
    db.add(a1)
    db.commit()
    db.add(a2)
    with pytest.raises(IntegrityError):
        db.commit()


def test_crawl_failure_creation(db):
    source = Source(name="Test", url="https://test.com/feed", type="rss", weight=5)
    db.add(source)
    db.commit()
    failure = CrawlFailure(source_id=source.id, url="https://test.com/article/1",
                           error_message="timeout", failed_at=datetime.now(timezone.utc))
    db.add(failure)
    db.commit()
    assert failure.retry_count == 0
    assert failure.resolved_at is None


def test_source_country_default(db):
    source = Source(name="Test Country", url="https://country.com/feed", type="rss", weight=7)
    db.add(source)
    db.commit()
    assert source.country == "global"


def test_source_country_kr(db):
    source = Source(name="KR Blog", url="https://kr-blog.com/feed", type="rss", weight=7, country="kr")
    db.add(source)
    db.commit()
    assert source.country == "kr"


def test_user_note_creation(db):
    source = Source(name="Test Note", url="https://note-test.com/feed", type="rss", weight=5)
    db.add(source)
    db.commit()
    article = Article(
        url="https://note-test.com/a/1",
        title="Test",
        source_id=source.id,
        score=50,
        score_breakdown="{}",
        tags="[]",
    )
    db.add(article)
    db.commit()

    note = UserNote(article_id=article.id)
    db.add(note)
    db.commit()

    assert note.is_bookmarked is False
    assert note.memo is None
    assert note.user_tags == "[]"
    assert note.created_at is not None


def test_user_note_unique_per_article(db):
    source = Source(name="Test Note 2", url="https://note-test2.com/feed", type="rss", weight=5)
    db.add(source)
    db.commit()
    article = Article(
        url="https://note-test2.com/a/1",
        title="Test",
        source_id=source.id,
        score=50,
        score_breakdown="{}",
        tags="[]",
    )
    db.add(article)
    db.commit()

    note1 = UserNote(article_id=article.id, is_bookmarked=True)
    note2 = UserNote(article_id=article.id)
    db.add(note1)
    db.commit()
    db.add(note2)
    with pytest.raises(IntegrityError):
        db.commit()
