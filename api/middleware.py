"""
FastAPI middleware: API key auth and request timing.
API key is read from the API_KEY environment variable.
Requests without a valid key return 401 (except /health and /docs).
"""
import os
import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

UNPROTECTED_PATHS = {"/health", "/docs", "/openapi.json"}
API_KEY = os.environ.get("API_KEY", "")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip auth for public paths
        if request.url.path in UNPROTECTED_PATHS:
            return await call_next(request)

        # Skip auth if no API_KEY is configured (dev mode)
        if not API_KEY:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {API_KEY}":
            return JSONResponse({"detail": "Invalid or missing API key."}, status_code=401)

        start = time.perf_counter()
        response = await call_next(request)
        ms = round((time.perf_counter() - start) * 1000)
        response.headers["X-Response-Time-Ms"] = str(ms)
        return response
