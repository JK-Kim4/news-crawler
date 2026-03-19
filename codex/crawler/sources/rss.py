from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import feedparser
import httpx
from crawler.sources.base import BaseCrawler, CrawledItem


class RssCrawler(BaseCrawler):
    def fetch(self) -> list[CrawledItem]:
        response = httpx.get(self.source_url, timeout=15, follow_redirects=True)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        return self.parse_feed(feed)

    def parse_feed(self, feed) -> list[CrawledItem]:
        items = []
        for entry in feed.entries:
            url = entry.get("link", "")
            if not url:
                continue
            title = entry.get("title", "")
            content = entry.get("summary", entry.get("description", ""))
            published_at = _parse_date(entry.get("published", ""))
            items.append(CrawledItem(url=url, title=title, content=content, published_at=published_at))
        return items


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None
