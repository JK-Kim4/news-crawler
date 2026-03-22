"""Duplicate detection: URL exact match + title similarity."""
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from app.db.models import Article

TITLE_SIMILARITY_THRESHOLD = 0.85


def is_duplicate(db: Session, url: str, title: str) -> bool:
    if db.query(Article.id).filter_by(url=url).first():
        return True
    recent_titles = (
        db.query(Article.title)
        .order_by(Article.crawled_at.desc())
        .limit(500)
        .all()
    )
    for (existing_title,) in recent_titles:
        if SequenceMatcher(None, title.strip(), existing_title.strip()).ratio() >= TITLE_SIMILARITY_THRESHOLD:
            return True
    return False
