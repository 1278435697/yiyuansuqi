"""路由注册。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import debug, garments, health, history, tryon

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["system"])
api_router.include_router(tryon.router, prefix="/tryon", tags=["tryon"])
api_router.include_router(garments.router, prefix="/garments", tags=["garments"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])

__all__ = ["api_router"]
