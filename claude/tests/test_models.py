from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from db.models import Article, Source, CrawlFailure, UserNote, User


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


def test_user_note_unique_per_user_and_article(db):
    """Same user cannot have two notes for the same article."""
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

    user = User(email="uniq@test.com", password_hash="h", nickname="u")
    db.add(user)
    db.commit()

    note1 = UserNote(article_id=article.id, user_id=user.id, is_bookmarked=True)
    note2 = UserNote(article_id=article.id, user_id=user.id)
    db.add(note1)
    db.commit()
    db.add(note2)
    with pytest.raises(IntegrityError):
        db.commit()


def test_user_creation(db):
    user = User(
        email="test@example.com",
        password_hash="hashed",
        nickname="tester",
        role="user",
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.role == "user"
    assert user.is_verified is False
    assert user.verify_token is None
    assert user.created_at is not None


def test_user_email_unique(db):
    u1 = User(email="dup@example.com", password_hash="h", nickname="a")
    u2 = User(email="dup@example.com", password_hash="h", nickname="b")
    db.add(u1)
    db.commit()
    db.add(u2)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()


def test_user_note_with_user_id(db):
    from db.models import Source, Article, UserNote
    user = User(email="u@test.com", password_hash="h", nickname="u")
    db.add(user)
    db.commit()
    source = Source(name="s", url="http://s.com", type="rss", weight=5)
    db.add(source)
    db.commit()
    article = Article(url="http://a.com", title="a", source_id=source.id)
    db.add(article)
    db.commit()
    note = UserNote(article_id=article.id, user_id=user.id)
    db.add(note)
    db.commit()
    assert note.user_id == user.id
