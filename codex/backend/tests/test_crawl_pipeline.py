from app.models.content import Content
from app.models.source import Source
from app.services.crawler import run_crawl


def test_crawl_pipeline_persists_summaries(db_session, monkeypatch):
    source = db_session.query(Source).first()

    def fake_parse(_url):
        return {
            "entries": [
                {
                    "title": "New AI Agent Release",
                    "link": "https://example.com/new-agent",
                    "summary": "<p>AI agents improve automation and workflow orchestration.</p>",
                    "author": "Reporter",
                    "published": "Tue, 24 Mar 2026 12:00:00 GMT",
                }
            ]
        }

    monkeypatch.setattr("app.services.crawler.feedparser.parse", fake_parse)

    job = run_crawl(db_session, [source.id], trigger="manual")
    stored = db_session.query(Content).filter(Content.original_url == "https://example.com/new-agent").one()

    assert job.status.value == "SUCCESS"
    assert stored.summary
    assert stored.tags

