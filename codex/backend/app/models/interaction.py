from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Bookmark(TimestampMixin, Base):
    __tablename__ = "bookmarks"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    content_id: Mapped[str] = mapped_column(ForeignKey("contents.id"), primary_key=True)

    user = relationship("User", back_populates="bookmarks")
    content = relationship("Content", back_populates="bookmarks")


class Comment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "comments"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    content_id: Mapped[str] = mapped_column(ForeignKey("contents.id"), index=True)
    content_text: Mapped[str] = mapped_column("content", Text)

    user = relationship("User", back_populates="comments")
    content = relationship("Content", back_populates="comments")

