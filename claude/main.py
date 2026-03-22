import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from api.articles import router as articles_router
from api.sources import router as sources_router
from auth.dependencies import LoginRequired
from auth.middleware import UserContextMiddleware
from auth.router import router as auth_router
from crawler.loader import load_and_sync_sources
from crawler.runner import CrawlRunner
from crawler.scheduler import start_scheduler, stop_scheduler
from db.session import SessionLocal, init_db

load_dotenv()

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


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    return RedirectResponse(url="/auth/login", status_code=303)


# Middleware order: outermost first. UserContext reads session, so Session must be added after (runs first).
app.add_middleware(UserContextMiddleware)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-secret-change-me"), max_age=604800)

app.include_router(auth_router)
app.include_router(articles_router)
app.include_router(sources_router)
