from pathlib import Path
from crawler.sources.scraper import ScraperCrawler

FIXTURE = Path(__file__).parent / "fixtures" / "sample_blog.html"

def test_scraper_parses_articles():
    html = FIXTURE.read_text()
    crawler = ScraperCrawler(source_url="https://blog.test.com")
    items = crawler.parse_html(html)
    assert len(items) == 2

def test_scraper_item_fields():
    html = FIXTURE.read_text()
    crawler = ScraperCrawler(source_url="https://blog.test.com")
    items = crawler.parse_html(html)
    first = items[0]
    assert first.url == "https://blog.test.com/posts/rag-tutorial"
    assert "RAG" in first.title or "RAG" in first.content
    assert first.published_at is not None
