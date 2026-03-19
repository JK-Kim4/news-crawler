from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CrawledItem:
    url: str
    title: str
    content: str
    published_at: datetime | None


class BaseCrawler(ABC):
    """모든 소스 크롤러의 공통 인터페이스."""

    def __init__(self, source_url: str) -> None:
        self.source_url = source_url

    @abstractmethod
    def fetch(self) -> list[CrawledItem]:
        """소스 URL에서 기사를 수집해 CrawledItem 목록으로 반환한다."""
