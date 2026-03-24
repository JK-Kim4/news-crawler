from app.services.source_config import load_source_configs


def test_source_config_loads_active_sources(tmp_path):
    source_file = tmp_path / "sources.json"
    source_file.write_text(
        """
        [
          {"key": "naver-d2", "name": "Naver D2", "base_url": "https://d2.naver.com", "rss_url": "https://d2.naver.com/feed", "selector_title": "h1", "selector_content": ".content", "language": "ko", "source_type": "BLOG", "is_active": true},
          {"key": "legacy", "name": "Legacy", "base_url": "https://legacy.example", "rss_url": null, "selector_title": "h1", "selector_content": ".body", "language": "en", "source_type": "NEWS", "is_active": false}
        ]
        """,
        encoding="utf-8",
    )

    sources = load_source_configs(source_file)

    assert len(sources) == 1
    assert sources[0].name == "Naver D2"
    assert sources[0].language == "ko"

