import json
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import SourceType
from app.models.source import Source


class SourceConfigRecord(BaseModel):
    key: str
    name: str
    base_url: str
    rss_url: str | None = None
    selector_title: str
    selector_content: str
    language: str = "ko"
    source_type: SourceType = SourceType.BLOG
    is_active: bool = True


def load_source_configs(path: Path | None = None) -> list[SourceConfigRecord]:
    source_path = path or get_settings().sources_path
    payload = json.loads(Path(source_path).read_text(encoding="utf-8"))
    return [SourceConfigRecord.model_validate(item) for item in payload if item.get("is_active", True)]


def sync_sources(db: Session, configs: list[SourceConfigRecord] | None = None) -> list[Source]:
    active_configs = configs or load_source_configs()
    existing = {
        source.key: source
        for source in db.scalars(select(Source)).all()
    }

    synced: list[Source] = []
    for config in active_configs:
        source = existing.get(config.key)
        if source is None:
            source = Source(**config.model_dump())
            db.add(source)
        else:
            for field, value in config.model_dump().items():
                setattr(source, field, value)
        synced.append(source)

    db.commit()
    for source in synced:
        db.refresh(source)
    return synced

