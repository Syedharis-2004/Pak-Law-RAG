"""
PakLaw AI — Audit Logging Middleware

Logs details of all modifying/sensitive HTTP requests to the audit trail database.
"""

import time
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.database import AsyncSessionLocal
from app.repositories.audit import AuditRepository
from app.models.audit import AuditLog
from app.core.logging_config import get_logger

logger = get_logger("audit")


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that captures metadata about requests and logs it to PostgreSQL.
    Only logs modifying methods (POST, PUT, DELETE, PATCH) or sensitive paths.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        
        # Track correlation ID if provided
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        # Forward the request
        response = await call_next(request)
        
        # Check if audit logging is required
        method = request.method
        path = request.url.path
        is_modifying = method in ("POST", "PUT", "DELETE", "PATCH")
        is_sensitive = path.startswith(("/api/v1/auth", "/api/v1/admin"))
        
        if is_modifying or is_sensitive:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Asynchronously write to audit log
            async with AsyncSessionLocal() as db:
                try:
                    # Resolve user identity if authenticated
                    user_id = None
                    auth_header = request.headers.get("Authorization")
                    if auth_header and auth_header.startswith("Bearer "):
                        try:
                            token = auth_header.split(" ")[1]
                            from app.core.security import decode_token
                            payload = decode_token(token)
                            user_id_str = payload.get("sub")
                            if user_id_str:
                                import uuid
                                user_id = uuid.UUID(user_id_str)
                        except Exception:
                            pass

                    # Extract basic resource classification
                    resource = "unknown"
                    parts = [p for p in path.split("/") if p]
                    if len(parts) >= 3:
                        resource = parts[2]  # e.g., /api/v1/documents -> documents

                    audit_repo = AuditRepository(AuditLog, db)
                    audit_in = {
                        "user_id": user_id,
                        "action": f"{method}_{path}",
                        "resource": resource,
                        "method": method,
                        "path": path,
                        "ip_address": request.client.host if request.client else "unknown",
                        "user_agent": request.headers.get("User-Agent"),
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "response_time_ms": duration_ms,
                    }
                    await audit_repo.create_audit_log(audit_in)
                    await db.commit()
                except Exception as e:
                    # Log error but do not disrupt client response
                    logger.error("Audit log storage failed", error=str(e))

        return response
