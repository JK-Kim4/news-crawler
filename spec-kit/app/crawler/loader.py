"""Load and sync sources from sources.json into DB."""
import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.models import Source

logger = logging.getLogger(__name__)


def load_and_sync_sources(db: Session, json_path: str = "config/sources.json"):
    path = Path(json_path)
    if not path.exists():
        logger.warning("Sources config not found: %s", json_path)
        return

    with open(path) as f:
        sources_data = json.load(f)

    for data in sources_data:
        existing = db.query(Source).filter_by(url=data["url"]).first()
        if existing:
            continue
        source = Source(
            name=data["name"],
            url=data["url"],
            type=data.get("type", "scraper"),
            category=data.get("category", "article"),
            weight=data.get("weight", 5),
            country=data.get("country", "kr"),
        )
        db.add(source)

    db.commit()
    logger.info("Synced %d sources from %s", len(sources_data), json_path)
