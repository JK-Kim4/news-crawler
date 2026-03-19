import feedparser
from pathlib import Path
from crawler.sources.rss import RssCrawler

FIXTURE = Path(__file__).parent / "fixtures" / "sample_rss.xml"

def test_rss_crawler_parses_items():
    feed_text = FIXTURE.read_text()
    feed = feedparser.parse(feed_text)
    crawler = RssCrawler(source_url="https://test.com/feed")
    items = crawler.parse_feed(feed)
    assert len(items) == 2

def test_rss_crawler_item_fields():
    feed_text = FIXTURE.read_text()
    feed = feedparser.parse(feed_text)
    crawler = RssCrawler(source_url="https://test.com/feed")
    items = crawler.parse_feed(feed)
    first = items[0]
    assert first.url == "https://test.com/articles/llm-benchmark"
    assert first.title == "New LLM Benchmark Results"
    assert "transformer" in first.content.lower() or "RAG" in first.content
    assert first.published_at is not None
