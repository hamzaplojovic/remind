"""Middleware for rate limiting and error tracking."""

import time
from typing import Callable, TypedDict
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from remind_backend.logging import get_logger

logger = get_logger(__name__)


class RateLimitBucket(TypedDict):
    """Rate limit bucket for tracking requests."""

    count: int
    reset_at: datetime


_request_counts: dict[str, RateLimitBucket] = defaultdict(
    lambda: {"count": 0, "reset_at": datetime.now(timezone.utc)}
)


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiting middleware by IP address."""

    async def dispatch(self, request: Request, call_next: Callable):
        from remind_backend.config import get_settings

        settings = get_settings()

        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        now = datetime.now(timezone.utc)
        bucket = _request_counts[client_ip]

        if now >= bucket["reset_at"]:
            bucket["count"] = 0
            bucket["reset_at"] = now + timedelta(
                seconds=settings.rate_limit_window_seconds
            )

        bucket["count"] += 1

        if bucket["count"] > settings.rate_limit_requests:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                count=bucket["count"],
                limit=settings.rate_limit_requests,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": int(
                        (bucket["reset_at"] - now).total_seconds()
                    ),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, settings.rate_limit_requests - bucket["count"])
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(bucket["reset_at"].timestamp())
        )

        return response


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """Error tracking middleware for monitoring and debugging."""

    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        request.state.request_id = request_id

        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            if duration > 5.0:
                logger.warning(
                    "slow_request",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    duration=f"{duration:.2f}s",
                    status_code=response.status_code,
                )

            if response.status_code >= 400:
                logger.warning(
                    "error_response",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration=f"{duration:.2f}s",
                )

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "unhandled_exception",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                duration=f"{duration:.2f}s",
                exc_info=True,
            )
            raise
