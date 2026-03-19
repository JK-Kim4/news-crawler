from datetime import datetime, timezone
from sqlalchemy import text
from crawler.pipeline import process_item
from crawler.sources.base import CrawledItem
from db.models import Article, Source

def _make_source(db, weight=8):
    source = Source(name="Test", url="https://test.com/feed", type="rss", weight=weight)
    db.add(source)
    db.commit()
    return source

def _make_item(url="https://test.com/1", title="LLM Tips", content="Using transformer and RAG"):
    return CrawledItem(url=url, title=title, content=content,
                       published_at=datetime.now(timezone.utc))

def test_process_item_saves_article(db):
    source = _make_source(db)
    item = _make_item()
    result = process_item(db, source, item)
    assert result is not None
    article = db.query(Article).filter_by(url=item.url).first()
    assert article is not None
    assert article.score > 0
    assert "LLM" in article.tags or "transformer" in article.tags

def test_process_item_skips_duplicate(db):
    source = _make_source(db)
    item = _make_item()
    process_item(db, source, item)
    result = process_item(db, source, item)  # same URL again
    assert result is None
    count = db.query(Article).filter_by(url=item.url).count()
    assert count == 1

def test_process_item_filters_non_ai(db):
    source = _make_source(db)
    item = _make_item(title="Docker Tutorial", content="How to use containers and pods")
    result = process_item(db, source, item)
    assert result is None
    count = db.query(Article).count()
    assert count == 0

def test_process_item_score_breakdown(db):
    source = _make_source(db, weight=10)
    item = _make_item()
    article = process_item(db, source, item)
    import json
    breakdown = json.loads(article.score_breakdown)
    assert "source" in breakdown
    assert "recency" in breakdown
    assert "keyword" in breakdown
    assert breakdown["source"] == 50


def test_process_item_syncs_fts(db):
    source = _make_source(db)
    item = _make_item(title="RAG Retrieval", content="RAG with transformer agents")

    article = process_item(db, source, item)

    row_ids = db.execute(
        text('SELECT rowid FROM article_fts WHERE article_fts MATCH \'"RAG"\'')
    ).scalars().all()

    assert article is not None
    assert article.id in row_ids
