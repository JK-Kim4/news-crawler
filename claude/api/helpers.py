import json
from sqlalchemy import func
from sqlalchemy.orm import Session
from db.models import Article, Source, UserNote


def parse_json_array(value):
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def parse_user_tags_input(raw):
    if not raw:
        return []
    seen = set()
    tags = []
    for part in raw.split(","):
        tag = part.strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def enrich_article(article: Article, user_id: int | None = None) -> Article:
    note = None
    if user_id is not None:
        from sqlalchemy.orm import object_session
        db = object_session(article)
        if db:
            note = db.query(UserNote).filter_by(article_id=article.id, user_id=user_id).first()
    article.tags_list = parse_json_array(article.tags)
    article.user_tags_list = parse_json_array(note.user_tags if note else "[]")
    article.memo_text = (note.memo or "").strip() if note and note.memo else ""
    article.memo_preview = (
        f"{article.memo_text[:50]}..." if len(article.memo_text) > 50 else article.memo_text
    )
    article.is_bookmarked = bool(note and note.is_bookmarked)
    article.country = article.source.country or "global"
    return article


def enrich_articles(articles, user_id=None):
    return [enrich_article(article, user_id) for article in articles]


def get_or_create_user_note(db: Session, article: Article, user_id: int) -> UserNote:
    note = db.query(UserNote).filter_by(article_id=article.id, user_id=user_id).first()
    if note:
        return note
    note = UserNote(article_id=article.id, user_id=user_id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def build_sidebar_context(db: Session, user=None):
    bookmark_count = 0
    if user:
        bookmark_count = db.query(UserNote).filter(
            UserNote.user_id == user.id,
            UserNote.is_bookmarked.is_(True),
        ).count()
    return {
        "nav_article_count": (
            db.query(Article)
            .join(Source)
            .filter(Source.is_active.is_(True))
            .count()
        ),
        "nav_bookmark_count": bookmark_count,
        "nav_source_count": db.query(Source).count(),
        "nav_last_crawled_at": db.query(func.max(Source.last_crawled_at)).scalar(),
    }
