import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.lib.logger import get_logger, log_event

logger = get_logger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log_event(
            logger,
            "request.completed",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params) or None,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_host=request.client.host if request.client else None,
            content_type=request.headers.get("content-type"),
            content_length=request.headers.get("content-length"),
            user_agent=request.headers.get("user-agent"),
        )

        return response
