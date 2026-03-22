"""Base parser interface and CrawledItem dataclass."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CrawledItem:
    url: str
    title: str
    content: str
    published_at: datetime | None = None


class BaseParser:
    """Base class for source-specific parsers."""

    def parse(self, html: str, source_url: str) -> list[CrawledItem]:
        raise NotImplementedError
