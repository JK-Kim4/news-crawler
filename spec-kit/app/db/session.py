import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.db.models import Base

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


def init_db():
    Base.metadata.create_all(engine)

    with engine.connect() as conn:
        # FTS5 virtual table for full-text search (trigram for Korean)
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

        # Rebuild FTS index
        try:
            conn.execute(text("INSERT INTO article_fts(article_fts) VALUES('rebuild')"))
            conn.commit()
        except Exception as e:
            logger.warning("FTS rebuild failed: %s", e)

        # Seed scoring_weights
        try:
            existing = conn.execute(text("SELECT COUNT(*) FROM scoring_weights")).scalar()
            if existing == 0:
                for key, weight, desc in [
                    ("source_trust", 1.0, "출처 신뢰도 가중치"),
                    ("recency", 1.0, "최신성 가중치"),
                    ("keyword", 1.0, "키워드 빈도 가중치"),
                    ("engagement", 0.5, "사용자 참여도(좋아요) 가중치"),
                ]:
                    conn.execute(
                        text("INSERT INTO scoring_weights (key, weight, description) VALUES (:k, :w, :d)"),
                        {"k": key, "w": weight, "d": desc},
                    )
                conn.commit()
                logger.info("Seeded scoring_weights with default values")
        except Exception as e:
            logger.warning("scoring_weights seed skipped: %s", e)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
