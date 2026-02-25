from fastapi import APIRouter

from .ai import router as ai_router
from .auth import router as auth_router
from .board import router as board_router
from .health import router as health_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(ai_router)
api_router.include_router(board_router)
api_router.include_router(health_router)
