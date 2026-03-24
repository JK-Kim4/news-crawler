import logging
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.content import Content
from app.services.source_manager import get_active_sources, get_source_by_name
from app.services.summarizer import summarize

logger = logging.getLogger(__name__)

_crawl_status: dict[str, Any] = {
    "is_running": False,
    "last_crawl_time": None,
    "last_results": [],
}


def get_crawl_status() -> dict[str, Any]:
    return _crawl_status.copy()


async def _url_exists(db: AsyncSession, url: str) -> bool:
    result = await db.execute(select(Content).where(Content.original_url == url))
    return result.scalar_one_or_none() is not None


async def _parse_rss_feed(source: dict) -> list[dict]:
    items = []
    rss_url = source.get("rss_url")
    if not rss_url:
        return items

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(rss_url, headers={"User-Agent": "NewsCrawler/1.0"})
            response.raise_for_status()

        feed = feedparser.parse(response.text)

        for entry in feed.entries[:20]:
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    pass
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                try:
                    published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    pass

            content_text = ""
            if hasattr(entry, "summary"):
                soup = BeautifulSoup(entry.summary, "html.parser")
                content_text = soup.get_text(strip=True)
            elif hasattr(entry, "content") and entry.content:
                soup = BeautifulSoup(entry.content[0].value, "html.parser")
                content_text = soup.get_text(strip=True)

            author = getattr(entry, "author", None)

            items.append({
                "title": entry.get("title", "Untitled"),
                "original_url": entry.get("link", ""),
                "published_at": published_at,
                "author": author,
                "raw_content": content_text,
            })

    except Exception as e:
        logger.error(f"RSS feed error for {source['name']}: {e}")

    return items


async def _parse_html_page(source: dict) -> list[dict]:
    items = []
    base_url = source.get("base_url")
    if not base_url:
        return items

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                base_url,
                headers={"User-Agent": "NewsCrawler/1.0"},
            )
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            title_el = a_tag.find(source.get("selector_title", "h2"))
            title_text = a_tag.get_text(strip=True) if not title_el else title_el.get_text(strip=True)

            if not title_text or len(title_text) < 5:
                continue

            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)

            if not href.startswith("http"):
                continue

            links.append({
                "title": title_text[:500],
                "original_url": href,
            })

        seen_urls = set()
        unique_links = []
        for link in links:
            if link["original_url"] not in seen_urls:
                seen_urls.add(link["original_url"])
                unique_links.append(link)

        for link_info in unique_links[:15]:
            try:
                async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                    detail_resp = await client.get(
                        link_info["original_url"],
                        headers={"User-Agent": "NewsCrawler/1.0"},
                    )
                    detail_resp.raise_for_status()

                detail_soup = BeautifulSoup(detail_resp.text, "html.parser")

                content_el = detail_soup.select_one(source.get("selector_content", "article"))
                raw_content = content_el.get_text(strip=True) if content_el else ""

                title_el = detail_soup.select_one(source.get("selector_title", "h1"))
                if title_el:
                    link_info["title"] = title_el.get_text(strip=True)[:500]

                items.append({
                    "title": link_info["title"],
                    "original_url": link_info["original_url"],
                    "published_at": None,
                    "author": None,
                    "raw_content": raw_content[:50000],
                })

            except Exception as e:
                logger.warning(f"Failed to fetch detail page {link_info['original_url']}: {e}")
                items.append({
                    "title": link_info["title"],
                    "original_url": link_info["original_url"],
                    "published_at": None,
                    "author": None,
                    "raw_content": "",
                })

    except Exception as e:
        logger.error(f"HTML crawl error for {source['name']}: {e}")

    return items


async def crawl_source(source: dict) -> dict[str, Any]:
    result = {
        "source_name": source["name"],
        "new_items": 0,
        "skipped_duplicates": 0,
        "errors": 0,
        "status": "success",
    }

    try:
        if source.get("rss_url"):
            items = await _parse_rss_feed(source)
        else:
            items = await _parse_html_page(source)

        async with async_session_factory() as db:
            for item in items:
                url = item.get("original_url", "").strip()
                if not url:
                    continue

                try:
                    if await _url_exists(db, url):
                        result["skipped_duplicates"] += 1
                        continue

                    summary_data = await summarize(
                        item.get("title", ""),
                        item.get("raw_content", ""),
                    )

                    content = Content(
                        source_type=source.get("source_type", "BLOG"),
                        source_name=source["name"],
                        title=item.get("title", "Untitled"),
                        original_url=url,
                        published_at=item.get("published_at"),
                        author=item.get("author"),
                        summary=summary_data.get("summary"),
                        tags=summary_data.get("tags", []),
                        raw_content=item.get("raw_content", ""),
                    )
                    db.add(content)
                    await db.commit()
                    result["new_items"] += 1

                except Exception as e:
                    await db.rollback()
                    logger.error(f"Error saving content from {source['name']}: {e}")
                    result["errors"] += 1

    except Exception as e:
        logger.error(f"Crawl failed for {source['name']}: {e}")
        result["status"] = "failed"
        result["error_message"] = str(e)

    return result


async def run_crawl(source_name: str | None = None) -> list[dict[str, Any]]:
    global _crawl_status

    if _crawl_status["is_running"]:
        return [{"status": "already_running", "message": "A crawl is already in progress"}]

    _crawl_status["is_running"] = True
    results = []

    try:
        if source_name:
            source = get_source_by_name(source_name)
            if source and source.get("is_active", True):
                result = await crawl_source(source)
                results.append(result)
            else:
                results.append({
                    "source_name": source_name,
                    "status": "not_found_or_inactive",
                })
        else:
            sources = get_active_sources()
            for source in sources:
                result = await crawl_source(source)
                results.append(result)
                logger.info(
                    f"Crawled {source['name']}: "
                    f"{result['new_items']} new, "
                    f"{result['skipped_duplicates']} skipped"
                )

    finally:
        _crawl_status["is_running"] = False
        _crawl_status["last_crawl_time"] = datetime.now(timezone.utc).isoformat()
        _crawl_status["last_results"] = results

    return results


async def scheduled_crawl():
    logger.info("Scheduled crawl starting...")
    results = await run_crawl()
    total_new = sum(r.get("new_items", 0) for r in results)
    logger.info(f"Scheduled crawl complete. Total new items: {total_new}")
