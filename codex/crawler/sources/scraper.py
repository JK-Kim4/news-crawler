from datetime import datetime
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from crawler.sources.base import BaseCrawler, CrawledItem


class ScraperCrawler(BaseCrawler):
    """범용 스크래퍼: <article> 태그와 <a href> + <time> 패턴을 파싱한다."""

    def fetch(self) -> list[CrawledItem]:
        response = httpx.get(self.source_url, timeout=15, follow_redirects=True)
        response.raise_for_status()
        return self.parse_html(response.text)

    def parse_html(self, html: str) -> list[CrawledItem]:
        soup = BeautifulSoup(html, "html.parser")
        items = []
        for article in soup.find_all("article"):
            link_tag = article.find("a", href=True)
            if not link_tag:
                continue
            url = _absolute_url(link_tag["href"], self.source_url)
            title = link_tag.get_text(strip=True)
            content = article.get_text(strip=True)
            time_tag = article.find("time")
            published_at = _parse_datetime(time_tag.get("datetime", "") if time_tag else "")
            items.append(CrawledItem(url=url, title=title, content=content, published_at=published_at))
        return items


def _absolute_url(href: str, base: str) -> str:
    """상대/프로토콜 상대 URL을 절대 URL로 변환한다."""
    return urljoin(base, href)


def _parse_datetime(dt_str: str) -> datetime | None:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None
