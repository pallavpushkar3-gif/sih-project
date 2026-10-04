"""Bounded error responses retain correlation IDs without leaking exception internals."""

import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("fleet.requests")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        from fleet_maintenance.settings import get_settings

        if request.method in {"POST", "PUT", "PATCH"}:
            limit = get_settings().maximum_request_bytes
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > limit:
                    return JSONResponse(
                        status_code=413, content={"detail": "Request body exceeds limit"}
                    )
            request._body = bytes(body)
        supplied = request.headers.get("x-request-id", "")
        correlation = (
            supplied if re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", supplied) else uuid.uuid4().hex
        )
        request.state.request_id = correlation
        started = time.monotonic()
        response = await call_next(request)
        response.headers["X-Request-ID"] = correlation
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request_finished",
            extra={
                "request_id": correlation,
                "method": request.method,
                "status": response.status_code,
                "duration_ms": round((time.monotonic() - started) * 1000, 2),
            },
        )
        return response


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unexpected(request: Request, error: Exception) -> JSONResponse:
        correlation = getattr(request.state, "request_id", uuid.uuid4().hex)
        logger.error(
            "request_failed request_id=%s error_type=%s", correlation, type(error).__name__
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred", "request_id": correlation},
            headers={"X-Request-ID": correlation, "Cache-Control": "no-store"},
        )
