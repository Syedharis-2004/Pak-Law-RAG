"""
PakLaw AI Backend — Custom Exception Hierarchy

Defines all application-specific exceptions and a global
FastAPI exception handler.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ── Base Exception ────────────────────────────────────────────
class PakLawException(Exception):
    """Base exception for all PakLaw AI application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


# ── Authentication Exceptions ─────────────────────────────────
class AuthenticationError(PakLawException):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR", status_code=401)


class AuthorizationError(PakLawException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, code="AUTHORIZATION_ERROR", status_code=403)


class TokenExpiredError(PakLawException):
    def __init__(self) -> None:
        super().__init__("Token has expired", code="TOKEN_EXPIRED", status_code=401)


class InvalidTokenError(PakLawException):
    def __init__(self) -> None:
        super().__init__("Invalid token", code="INVALID_TOKEN", status_code=401)


# ── Resource Exceptions ───────────────────────────────────────
class NotFoundError(PakLawException):
    def __init__(self, resource: str = "Resource", resource_id: str | None = None) -> None:
        msg = f"{resource} not found"
        if resource_id:
            msg = f"{resource} with id '{resource_id}' not found"
        super().__init__(msg, code="NOT_FOUND", status_code=404)


class ConflictError(PakLawException):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, code="CONFLICT", status_code=409)


class ValidationError(PakLawException):
    def __init__(self, message: str, field: str | None = None) -> None:
        details = {"field": field} if field else {}
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, details=details)


# ── Document Exceptions ───────────────────────────────────────
class DocumentProcessingError(PakLawException):
    def __init__(self, message: str, document_id: str | None = None) -> None:
        details = {"document_id": document_id} if document_id else {}
        super().__init__(
            message, code="DOCUMENT_PROCESSING_ERROR", status_code=500, details=details
        )


class UnsupportedFileTypeError(PakLawException):
    def __init__(self, file_type: str) -> None:
        super().__init__(
            f"File type '{file_type}' is not supported",
            code="UNSUPPORTED_FILE_TYPE",
            status_code=415,
            details={"file_type": file_type},
        )


class FileTooLargeError(PakLawException):
    def __init__(self, max_size_mb: int) -> None:
        super().__init__(
            f"File exceeds maximum size of {max_size_mb}MB",
            code="FILE_TOO_LARGE",
            status_code=413,
            details={"max_size_mb": max_size_mb},
        )


# ── AI/RAG Exceptions ─────────────────────────────────────────
class LLMError(PakLawException):
    def __init__(self, message: str = "LLM inference failed") -> None:
        super().__init__(message, code="LLM_ERROR", status_code=503)


class EmbeddingError(PakLawException):
    def __init__(self, message: str = "Embedding generation failed") -> None:
        super().__init__(message, code="EMBEDDING_ERROR", status_code=503)


class RetrievalError(PakLawException):
    def __init__(self, message: str = "Document retrieval failed") -> None:
        super().__init__(message, code="RETRIEVAL_ERROR", status_code=503)


class InsufficientEvidenceError(PakLawException):
    def __init__(self) -> None:
        super().__init__(
            "Insufficient legal evidence found to answer this question. "
            "Please ensure relevant documents have been indexed.",
            code="INSUFFICIENT_EVIDENCE",
            status_code=422,
        )


# ── Rate Limit Exception ──────────────────────────────────────
class RateLimitError(PakLawException):
    def __init__(self) -> None:
        super().__init__(
            "Rate limit exceeded. Please try again later.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )


# ── Global Exception Handler Registration ────────────────────
def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(PakLawException)
    async def paklawai_exception_handler(
        request: Request, exc: PakLawException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again.",
                    "details": {},
                }
            },
        )
