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


def enrich_article(article: Article) -> Article:
    note = article.user_note
    article.tags_list = parse_json_array(article.tags)
    article.user_tags_list = parse_json_array(note.user_tags if note else "[]")
    article.memo_text = (note.memo or "").strip() if note and note.memo else ""
    article.memo_preview = (
        f"{article.memo_text[:50]}..." if len(article.memo_text) > 50 else article.memo_text
    )
    article.is_bookmarked = bool(note and note.is_bookmarked)
    article.country = article.source.country or "global"
    return article


def enrich_articles(articles):
    return [enrich_article(article) for article in articles]


def get_or_create_user_note(db: Session, article: Article) -> UserNote:
    note = article.user_note
    if note:
        return note
    note = UserNote(article_id=article.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    db.refresh(article)
    return article.user_note


def build_sidebar_context(db: Session):
    return {
        "nav_article_count": (
            db.query(Article)
            .join(Source)
            .filter(Source.is_active.is_(True))
            .count()
        ),
        "nav_bookmark_count": db.query(UserNote).filter(UserNote.is_bookmarked.is_(True)).count(),
        "nav_source_count": db.query(Source).count(),
        "nav_last_crawled_at": db.query(func.max(Source.last_crawled_at)).scalar(),
    }
