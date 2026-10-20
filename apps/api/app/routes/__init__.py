"""API routes package."""
from fastapi import APIRouter
from apps.api.app.auth import router as auth_router
from apps.api.app.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)

__all__ = ["api_router"]
