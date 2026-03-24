from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import SourceType


class Content(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "contents"

    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"), nullable=True, index=True)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType))
    source_name: Mapped[str] = mapped_column(String(255), index=True)
    language: Mapped[str] = mapped_column(String(10), default="ko", index=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    original_url: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    crawled_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    source = relationship("Source", back_populates="contents")
    bookmarks = relationship("Bookmark", back_populates="content", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="content", cascade="all, delete-orphan")

