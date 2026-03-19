import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_fts():
    """FTS5 가상 테이블이 포함된 인메모리 DB 픽스처."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
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
    Session = sessionmaker(engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()
