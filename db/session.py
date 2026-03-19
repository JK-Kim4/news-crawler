import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base

logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_news.db")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


def init_db():
    Base.metadata.create_all(engine)

    with engine.connect() as conn:
        # sources 테이블에 country 컬럼 추가 (기존 DB 마이그레이션)
        try:
            conn.execute(text("ALTER TABLE sources ADD COLUMN country TEXT DEFAULT 'global'"))
            conn.commit()
        except Exception:
            pass  # 컬럼이 이미 존재하면 무시

        # FTS5 가상 테이블 생성 (trigram tokenizer로 한국어 포함 검색 지원)
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

        # 기존 데이터 FTS 인덱싱 (rebuild은 멱등적으로 동작)
        try:
            conn.execute(text("INSERT INTO article_fts(article_fts) VALUES('rebuild')"))
            conn.commit()
        except Exception as e:
            logger.warning("FTS rebuild failed: %s", e)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
