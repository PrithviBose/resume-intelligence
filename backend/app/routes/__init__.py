from fastapi import APIRouter

from app.routes import analyze, health, parse, search, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(analyze.router)
api_router.include_router(parse.router)
api_router.include_router(search.router)
api_router.include_router(users.router)

__all__ = ["api_router"]
