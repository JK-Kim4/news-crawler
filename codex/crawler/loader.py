import json
from sqlalchemy.orm import Session
from db.models import Source


class SourceConfigError(Exception):
    pass


def load_and_sync_sources(db: Session | None, config_path: str) -> None:
    """sources.json을 읽어 DB와 동기화한다.

    - weight가 1~10 범위를 벗어나면 SourceConfigError 발생
    - 필수 필드(url, name, type) 누락 시 SourceConfigError 발생
    - db=None이면 검증만 수행하고 DB 조작 없이 반환
    """
    with open(config_path) as f:
        config = json.load(f)

    entries = config.get("sources", [])
    required_fields = ("url", "name", "type", "weight")
    for entry in entries:
        missing = [f for f in required_fields if f not in entry]
        if missing:
            raise SourceConfigError(
                f"소스 항목에 필수 필드가 없습니다: {missing} — {entry}"
            )
        weight = entry["weight"]
        if not (1 <= weight <= 10):
            raise SourceConfigError(
                f"Invalid weight {weight} for source '{entry['name']}'. Must be 1-10."
            )
        country = entry.get("country", "global")
        if country not in {"kr", "global"}:
            raise SourceConfigError(
                f"Invalid country {country!r} for source '{entry['name']}'. Must be 'kr' or 'global'."
            )

    if db is None:
        return  # 검증만 수행

    config_urls = {e["url"] for e in entries}
    existing: dict[str, Source] = {
        s.url: s for s in db.query(Source).all()
    }

    for entry in entries:
        url = entry["url"]
        if url in existing:
            src = existing[url]
            src.name = entry["name"]
            src.type = entry["type"]
            src.weight = entry["weight"]
            src.country = entry.get("country", "global")
        else:
            db.add(Source(
                name=entry["name"],
                url=url,
                type=entry["type"],
                weight=entry["weight"],
                country=entry.get("country", "global"),
            ))

    # sources.json에서 제거된 소스는 비활성화 (데이터 보존)
    for url, src in existing.items():
        if url not in config_urls:
            src.is_active = False

    db.commit()
