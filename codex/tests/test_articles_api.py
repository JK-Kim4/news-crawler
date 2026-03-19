from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from api.articles import router as articles_router
from api.sources import router as sources_router
from db.models import Article, Base, Source, UserNote
from db.session import get_db


def _enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def _build_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", _enable_foreign_keys)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS article_fts
            USING fts5(
                title, content,
                content='articles',
                content_rowid='id',
                tokenize='trigram'
            )
        """))

    SessionLocal = sessionmaker(engine)
    app = FastAPI()
    app.include_router(articles_router)
    app.include_router(sources_router)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), SessionLocal, engine


def test_bookmark_toggle_creates_note():
    client, SessionLocal, engine = _build_client()
    with SessionLocal() as db:
        source = Source(name="OpenAI", url="https://openai.com/blog", type="rss", weight=9, country="global")
        db.add(source)
        db.commit()
        article = Article(
            url="https://openai.com/blog/test",
            title="Agentic RAG",
            content="Agent systems with RAG",
            tags='["RAG"]',
            source_id=source.id,
            score=91,
            score_breakdown="{}",
            published_at=datetime.now(timezone.utc),
        )
        db.add(article)
        db.commit()
        article_id = article.id

    response = client.post(f"/articles/{article_id}/bookmark")
    assert response.status_code == 200

    with SessionLocal() as db:
        note = db.query(UserNote).filter_by(article_id=article_id).first()
        assert note is not None
        assert note.is_bookmarked is True
    engine.dispose()


def test_search_page_uses_fts():
    client, SessionLocal, engine = _build_client()
    with SessionLocal() as db:
        source = Source(name="HF", url="https://hf.co/feed", type="rss", weight=8, country="global")
        db.add(source)
        db.commit()
        article = Article(
            url="https://hf.co/blog/rag",
            title="RAG Systems in Production",
            content="RAG pipelines for reliable agents",
            tags='["RAG"]',
            source_id=source.id,
            score=88,
            score_breakdown="{}",
            published_at=datetime.now(timezone.utc),
        )
        db.add(article)
        db.commit()
        db.execute(
            text("INSERT INTO article_fts(rowid, title, content) VALUES (:id, :title, :content)"),
            {"id": article.id, "title": article.title, "content": article.content},
        )
        db.commit()

    response = client.get("/search?q=RAG&country=global")
    assert response.status_code == 200
    assert "RAG Systems in Production" in response.text
    engine.dispose()


def test_translate_kr_article_returns_400():
    client, SessionLocal, engine = _build_client()
    with SessionLocal() as db:
        source = Source(name="KR", url="https://kr.example/feed", type="rss", weight=7, country="kr")
        db.add(source)
        db.commit()
        article = Article(
            url="https://kr.example/post",
            title="한국어 글",
            content="이미 한국어인 본문",
            tags='["AI"]',
            source_id=source.id,
            score=77,
            score_breakdown="{}",
            published_at=datetime.now(timezone.utc),
        )
        db.add(article)
        db.commit()
        article_id = article.id

    response = client.post(f"/articles/{article_id}/translate")
    assert response.status_code == 400
    assert "번역 대상" in response.text
    engine.dispose()


def test_translate_global_article_renders_result(monkeypatch):
    client, SessionLocal, engine = _build_client()
    with SessionLocal() as db:
        source = Source(name="Global", url="https://global.example/feed", type="rss", weight=7, country="global")
        db.add(source)
        db.commit()
        article = Article(
            url="https://global.example/post",
            title="Global article",
            content="This is an English article about AI agents.",
            tags='["agent"]',
            source_id=source.id,
            score=80,
            score_breakdown="{}",
            published_at=datetime.now(timezone.utc),
        )
        db.add(article)
        db.commit()
        article_id = article.id

    monkeypatch.setattr("api.articles._translate_text", lambda value: "번역된 결과")
    response = client.post(f"/articles/{article_id}/translate")
    assert response.status_code == 200
    assert "번역된 결과" in response.text
    engine.dispose()
