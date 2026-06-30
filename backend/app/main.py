from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.lib.config import settings
from app.lib.database import init_db
from app.lib.logging_config import configure_logging_from_settings
from app.lib.logger import get_logger, log_event
from app.middleware.cors import setup_cors
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routes import api_router

configure_logging_from_settings(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        log_event(logger, "database.initialized")
    except Exception as exc:
        log_event(
            logger,
            "database.initialization_failed",
            level=40,
            error=str(exc),
        )
    yield


app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
)

setup_cors(app)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(api_router)
