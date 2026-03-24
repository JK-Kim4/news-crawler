from fastapi import APIRouter

from app.api import admin, auth, content, health, user


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(content.router)
api_router.include_router(user.router)
api_router.include_router(admin.router)

