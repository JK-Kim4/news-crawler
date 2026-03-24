from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _engine_kwargs(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


def build_engine(database_url: str):
    return create_engine(database_url, **_engine_kwargs(database_url))


def build_session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


settings = get_settings()
engine = build_engine(settings.database_url)
SessionLocal = build_session_factory(engine)


def configure_database(database_url: str) -> None:
    global engine, SessionLocal
    engine = build_engine(database_url)
    SessionLocal.configure(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db.base import Base
    from app.models import crawl_job, notification, content, interaction, source, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
