import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal, configure_database, init_db
from app.main import create_app
from app.services.source_config import sync_sources


@pytest.fixture()
def app(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(
        json.dumps(
            [
                {
                    "key": "test-source",
                    "name": "Test Source",
                    "base_url": "https://example.com",
                    "rss_url": "https://example.com/feed.xml",
                    "selector_title": "h1",
                    "selector_content": ".content",
                    "language": "ko",
                    "source_type": "BLOG",
                    "is_active": True,
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("AINSIGHTS_DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("AINSIGHTS_SOURCES_PATH", str(sources_path))
    monkeypatch.setenv("AINSIGHTS_SECRET_KEY", "test-secret-key-with-minimum-32-bytes")
    get_settings.cache_clear()
    settings = get_settings()
    configure_database(settings.database_url)
    init_db()
    db = SessionLocal()
    try:
        sync_sources(db)
    finally:
        db.close()
    return create_app()


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(app) -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
