from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.content import Content
from app.models.crawl_job import CrawlJob
from app.models.interaction import Bookmark, Comment
from app.models.notification import NotificationPreference
from app.models.source import Source
from app.models.user import User


def list_contents(
    db: Session,
    *,
    q: str | None = None,
    language: str | None = None,
    source_name: str | None = None,
    source_type: str | None = None,
) -> list[Content]:
    stmt = select(Content).order_by(Content.published_at.desc().nullslast(), Content.created_at.desc())
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where((Content.title.ilike(pattern)) | (Content.summary.ilike(pattern)))
    if language:
        stmt = stmt.where(Content.language == language)
    if source_name:
        stmt = stmt.where(Content.source_name == source_name)
    if source_type:
        stmt = stmt.where(Content.source_type == source_type)
    return list(db.scalars(stmt).all())


def get_content(db: Session, content_id: str) -> Content | None:
    stmt = (
        select(Content)
        .where(Content.id == content_id)
        .options(joinedload(Content.comments).joinedload(Comment.user))
    )
    return db.scalar(stmt)


def list_bookmarks(db: Session, user_id: str) -> list[Content]:
    stmt = (
        select(Content)
        .join(Bookmark, Bookmark.content_id == Content.id)
        .where(Bookmark.user_id == user_id)
        .order_by(Content.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def set_bookmark(db: Session, user_id: str, content_id: str, enabled: bool) -> None:
    bookmark = db.scalar(select(Bookmark).where(Bookmark.user_id == user_id, Bookmark.content_id == content_id))
    if enabled and bookmark is None:
        db.add(Bookmark(user_id=user_id, content_id=content_id))
    elif not enabled and bookmark is not None:
        db.delete(bookmark)
    db.commit()


def add_comment(db: Session, user_id: str, content_id: str, comment_text: str) -> Comment:
    comment = Comment(user_id=user_id, content_id=content_id, content_text=comment_text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment_id: str) -> Comment | None:
    comment = db.get(Comment, comment_id)
    if comment is None:
        return None
    db.delete(comment)
    db.commit()
    return comment


def get_notification_preference(db: Session, user_id: str) -> NotificationPreference:
    preference = db.scalar(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
    if preference is None:
        preference = NotificationPreference(user_id=user_id, keywords=[])
        db.add(preference)
        db.commit()
        db.refresh(preference)
    return preference


def update_notification_preference(
    db: Session,
    user_id: str,
    *,
    keywords: list[str],
    email_enabled: bool,
    slack_enabled: bool,
) -> NotificationPreference:
    preference = get_notification_preference(db, user_id)
    preference.keywords = keywords
    preference.email_enabled = email_enabled
    preference.slack_enabled = slack_enabled
    db.commit()
    db.refresh(preference)
    return preference


def admin_overview(db: Session) -> dict:
    last_crawl = db.scalar(select(CrawlJob).order_by(CrawlJob.started_at.desc()))
    return {
        "total_users": db.scalar(select(func.count()).select_from(User)) or 0,
        "total_contents": db.scalar(select(func.count()).select_from(Content)) or 0,
        "total_sources": db.scalar(select(func.count()).select_from(Source)) or 0,
        "active_sources": db.scalar(select(func.count()).select_from(Source).where(Source.is_active.is_(True))) or 0,
        "last_crawl_status": last_crawl.status.value if last_crawl else None,
        "last_crawl_at": last_crawl.started_at if last_crawl else None,
    }

