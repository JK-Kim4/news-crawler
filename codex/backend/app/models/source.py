from datetime import UTC, datetime

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import SourceType


class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sources"

    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    base_url: Mapped[str] = mapped_column(String(500))
    rss_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    selector_title: Mapped[str] = mapped_column(String(255))
    selector_content: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(10), default="ko", index=True)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), default=SourceType.BLOG)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    contents = relationship("Content", back_populates="source")

