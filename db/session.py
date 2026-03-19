import logging
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

logger = logging.getLogger(__name__)
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_news.db")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def init_db():
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE sources ADD COLUMN country TEXT DEFAULT 'global'"))
            conn.commit()
        except Exception:
            conn.rollback()

        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS article_fts
            USING fts5(
                title, content,
                content='articles',
                content_rowid='id',
                tokenize='trigram'
            )
        """))
        conn.commit()

        try:
            conn.execute(text("INSERT INTO article_fts(article_fts) VALUES('rebuild')"))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.warning("FTS rebuild failed: %s", exc)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
