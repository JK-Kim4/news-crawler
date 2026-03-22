from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    url = Column(String(2048), unique=True, nullable=False)
    type = Column(String(20), nullable=False)  # "rss" | "scraper"
    category = Column(String(20), default="article", nullable=False)  # "article" | "paper" | "blog"
    weight = Column(Float, default=5.0)
    country = Column(String(10), default="kr", nullable=False)
    crawl_interval_hours = Column(Integer, default=24)
    is_active = Column(Boolean, default=True)
    last_crawled_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    articles = relationship("Article", back_populates="source")
    failures = relationship("CrawlFailure", back_populates="source")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    url = Column(String(2048), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    tags = Column(Text, default="[]")
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    category = Column(String(20), default="article", nullable=False)
    score = Column(Integer, default=0)
    score_breakdown = Column(Text, default="{}")
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    crawled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Boolean, default=False, nullable=False)

    source = relationship("Source", back_populates="articles")
    scraps = relationship("Scrap", back_populates="article", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="article", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="article", cascade="all, delete-orphan")


class Scrap(Base):
    __tablename__ = "scraps"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_scrap_user_article"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    article = relationship("Article", back_populates="scraps")


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_like_user_article"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    article = relationship("Article", back_populates="likes")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    is_edited = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    article = relationship("Article", back_populates="comments")


class ScoringWeight(Base):
    __tablename__ = "scoring_weights"

    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    weight = Column(Float, default=1.0, nullable=False)
    description = Column(String(200), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class CrawlFailure(Base):
    __tablename__ = "crawl_failures"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    url = Column(String(2048), nullable=True)
    error_message = Column(Text, nullable=False)
    failed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    retry_count = Column(Integer, default=0)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    source = relationship("Source", back_populates="failures")
