import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.auth.dependencies import LoginRequired
from app.auth.middleware import UserContextMiddleware
from app.auth.router import router as auth_router
from app.api.articles import router as articles_router
from app.api.likes import router as likes_router
from app.api.comments import router as comments_router
from app.api.scraps import router as scraps_router
from app.api.admin import router as admin_router
from app.config import SECRET_KEY
from app.db.session import init_db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI News Crawler", lifespan=lifespan)


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    return RedirectResponse(url="/auth/login", status_code=303)


app.add_middleware(UserContextMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=604800)

app.include_router(auth_router)
app.include_router(articles_router)
app.include_router(likes_router)
app.include_router(comments_router)
app.include_router(scraps_router)
app.include_router(admin_router)
