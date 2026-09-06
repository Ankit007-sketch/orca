"""
API Middleware for ORCA Backend (SIH26176)
Provides CORS configuration, execution timing, structured error handling,
and rate limiting logging.
"""

import time
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("orca.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class ProcessTimeAndLoggingMiddleware(BaseHTTPMiddleware):
    """Measures API execution time and adds X-Process-Time header."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000.0
            response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
            logger.info(f"{method} {path} - Status: {response.status_code} ({process_time:.2f}ms)")
            return response
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000.0
            logger.error(f"{method} {path} Failed after {process_time:.2f}ms - Exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": str(exc),
                    "path": path,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            )


def setup_cors_origins():
    """Returns list of allowed CORS origins for development & production."""
    return [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "*"
    ]
