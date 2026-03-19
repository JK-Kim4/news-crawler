import json
import pytest
from crawler.loader import load_and_sync_sources, SourceConfigError


VALID_CONFIG = {
    "sources": [
        {"name": "Test RSS", "url": "https://test.com/feed", "type": "rss", "weight": 8, "country": "kr"},
        {"name": "Test Scraper", "url": "https://blog.test.com", "type": "scraper", "weight": 5},
    ]
}


def test_insert_new_sources(db, tmp_path):
    config_file = tmp_path / "sources.json"
    config_file.write_text(json.dumps(VALID_CONFIG))
    load_and_sync_sources(db, str(config_file))
    from db.models import Source
    sources = db.query(Source).all()
    assert len(sources) == 2
    assert sources[0].name == "Test RSS"
    assert sources[0].is_active is True
    assert sources[0].country == "kr"
    assert sources[1].country == "global"


def test_update_existing_source(db, tmp_path):
    from db.models import Source
    existing = Source(name="Old Name", url="https://test.com/feed", type="rss", weight=5)
    db.add(existing)
    db.commit()

    config_file = tmp_path / "sources.json"
    config_file.write_text(json.dumps(VALID_CONFIG))
    load_and_sync_sources(db, str(config_file))

    db.refresh(existing)
    assert existing.name == "Test RSS"
    assert existing.weight == 8
    assert existing.country == "kr"
    assert existing.is_active is True  # runtime state preserved


def test_deactivate_removed_source(db, tmp_path):
    from db.models import Source
    removed = Source(name="Removed", url="https://removed.com/feed", type="rss", weight=5)
    db.add(removed)
    db.commit()

    config_file = tmp_path / "sources.json"
    config_file.write_text(json.dumps(VALID_CONFIG))
    load_and_sync_sources(db, str(config_file))

    db.refresh(removed)
    assert removed.is_active is False


def test_invalid_weight_raises(tmp_path):
    config_file = tmp_path / "sources.json"
    config_file.write_text(json.dumps({
        "sources": [{"name": "Bad", "url": "https://x.com", "type": "rss", "weight": 11}]
    }))
    with pytest.raises(SourceConfigError):
        load_and_sync_sources(None, str(config_file))


def test_invalid_country_raises(tmp_path):
    config_file = tmp_path / "sources.json"
    config_file.write_text(json.dumps({
        "sources": [{"name": "Bad", "url": "https://x.com", "type": "rss", "weight": 5, "country": "jp"}]
    }))
    with pytest.raises(SourceConfigError):
        load_and_sync_sources(None, str(config_file))
