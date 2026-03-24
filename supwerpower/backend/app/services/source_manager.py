import json
import os
from pathlib import Path
from typing import Any

SOURCES_FILE = Path(__file__).resolve().parent.parent.parent / "sources.json"


def _read_sources_file() -> dict:
    if not SOURCES_FILE.exists():
        return {"sources": []}
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_sources_file(data: dict) -> None:
    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_all_sources() -> list[dict]:
    data = _read_sources_file()
    return data.get("sources", [])


def get_active_sources() -> list[dict]:
    return [s for s in get_all_sources() if s.get("is_active", True)]


def get_source_by_name(name: str) -> dict | None:
    for source in get_all_sources():
        if source["name"] == name:
            return source
    return None


def update_source(name: str, updates: dict[str, Any]) -> dict | None:
    data = _read_sources_file()
    sources = data.get("sources", [])
    for i, source in enumerate(sources):
        if source["name"] == name:
            sources[i].update(updates)
            sources[i]["name"] = name
            data["sources"] = sources
            _write_sources_file(data)
            return sources[i]
    return None


def add_source(source: dict) -> dict:
    data = _read_sources_file()
    sources = data.get("sources", [])
    for existing in sources:
        if existing["name"] == source["name"]:
            raise ValueError(f"Source '{source['name']}' already exists")
    sources.append(source)
    data["sources"] = sources
    _write_sources_file(data)
    return source


def delete_source(name: str) -> bool:
    data = _read_sources_file()
    sources = data.get("sources", [])
    original_len = len(sources)
    sources = [s for s in sources if s["name"] != name]
    if len(sources) == original_len:
        return False
    data["sources"] = sources
    _write_sources_file(data)
    return True
