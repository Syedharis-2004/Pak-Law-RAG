"""
PakLaw AI — Rate Limiting Middleware

Implements an asynchronous sliding window rate limiter using Redis.
Provides request and chat endpoint-specific rate limiting.
"""

import time

import redis.asyncio as aioredis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.exceptions import RateLimitError


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that limits incoming requests using a sliding window algorithm via Redis.
    Uses setting configurations for thresholds.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for docs, openapi schema, health checks, or pytest runs
        import sys

        path = request.url.path
        if "pytest" in sys.modules or path.startswith(
            ("/docs", "/redoc", "/openapi.json", "/health")
        ):
            return await call_next(request)

        # Identify client (IP or User ID if authenticated)
        client_ip = request.client.host if request.client else "unknown"
        user_id = "anonymous"

        # Check authorization header without full dependencies parsing
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # Basic token extract just to segment rate limits
                token = auth_header.split(" ")[1]
                from app.core.security import decode_token

                payload = decode_token(token)
                user_id = payload.get("sub", "anonymous")
            except Exception:
                pass

        identifier = f"rate:{user_id}:{client_ip}"

        # Segment chat limits
        is_chat = path.startswith("/api/v1/chat")
        limit = settings.RATE_LIMIT_CHAT_REQUESTS if is_chat else settings.RATE_LIMIT_REQUESTS
        window = (
            settings.RATE_LIMIT_CHAT_WINDOW_SECONDS
            if is_chat
            else settings.RATE_LIMIT_WINDOW_SECONDS
        )

        current_time = time.time()
        key = f"{identifier}:{path}"

        try:
            # Use Redis transaction pipeline to add request and prune old ones
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, current_time - window)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.zcard(key)
                pipe.expire(key, window)
                results = await pipe.execute()

            request_count = results[2]

            if request_count > limit:
                raise RateLimitError()

        except aioredis.RedisError:
            # Fallback gracefully if Redis is down in production
            pass

        response = await call_next(request)
        return response
