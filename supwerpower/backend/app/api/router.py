from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.content import router as content_router
from app.api.admin import router as admin_router
from app.api.user import router as user_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(content_router)
api_router.include_router(admin_router)
api_router.include_router(user_router)
