import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.articles import router as articles_router
from api.sources import router as sources_router
from crawler.loader import load_and_sync_sources
from crawler.runner import CrawlRunner
from crawler.scheduler import start_scheduler, stop_scheduler
from db.session import SessionLocal, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)


def scheduled_crawl():
    db = SessionLocal()
    try:
        CrawlRunner(db).run()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        load_and_sync_sources(db, "config/sources.json")
    finally:
        db.close()
    start_scheduler(scheduled_crawl)
    yield
    stop_scheduler()


app = FastAPI(title="AI Archive", lifespan=lifespan)
app.include_router(articles_router)
app.include_router(sources_router)
