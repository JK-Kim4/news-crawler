from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False)  # "rss" | "scraper"
    weight = Column(Integer, nullable=False, default=5)
    country = Column(String(10), default="global", nullable=False)  # "kr" | "global"
    crawl_interval_hours = Column(Integer, default=6)  # reserved for v2
    is_active = Column(Boolean, default=True)
    last_crawled_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    articles = relationship("Article", back_populates="source")
    failures = relationship("CrawlFailure", back_populates="source")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    tags = Column(Text, default="[]")        # JSON 배열 문자열
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    score = Column(Integer, default=0)
    score_breakdown = Column(Text, default="{}")  # JSON 문자열
    published_at = Column(DateTime(timezone=True), nullable=True)
    crawled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_read = Column(Boolean, default=False)

    source = relationship("Source", back_populates="articles")
    user_note = relationship(
        "UserNote",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserNote(Base):
    __tablename__ = "user_notes"

    id = Column(Integer, primary_key=True)
    article_id = Column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    is_bookmarked = Column(Boolean, default=False, nullable=False)
    memo = Column(Text, nullable=True)
    user_tags = Column(Text, default="[]", nullable=False)  # JSON 배열 문자열
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    article = relationship("Article", back_populates="user_note")


class CrawlFailure(Base):
    __tablename__ = "crawl_failures"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    url = Column(String, nullable=True)       # None이면 소스 전체 실패
    error_message = Column(Text, nullable=False)
    failed_at = Column(DateTime(timezone=True), nullable=False)
    retry_count = Column(Integer, default=0)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    source = relationship("Source", back_populates="failures")
