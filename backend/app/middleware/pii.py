"""
PakLaw AI — PII Detection & Data Protection Middleware

Detects and masks Personally Identifiable Information (PII) like CNIC,
phone numbers, and email addresses in outgoing responses.
"""

import re
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# Regex patterns for Pakistani PII detection
# CNIC: 5 digits - 7 digits - 1 digit
CNIC_PATTERN = re.compile(r"\b\d{5}-\d{7}-\d{1}\b")
# Phone: Mobile numbers starting with 03xx or +923xx
PHONE_PATTERN = re.compile(r"\b(?:\+92|0)?3\d{2}[- ]?\d{7}\b")
# Email Address
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")


class PIIDetectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that scans and redacts PII in outgoing JSON API responses.
    This ensures no PII is accidentally leaked through LLM completion outputs or database extracts.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Scan and clean only JSON responses to avoid disrupting file downloads
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            text = body.decode("utf-8")
            
            # Mask sensitive PII parameters
            cleaned_text = CNIC_PATTERN.sub("[CNIC_MASKED]", text)
            cleaned_text = PHONE_PATTERN.sub("[PHONE_MASKED]", cleaned_text)
            cleaned_text = EMAIL_PATTERN.sub("[EMAIL_MASKED]", cleaned_text)
            
            new_body = cleaned_text.encode("utf-8")
            response.headers["content-length"] = str(len(new_body))
            
            # Reconstruct response body iterator
            async def new_body_iterator():
                yield new_body
            
            response.body_iterator = new_body_iterator()
        except Exception:
            # Fallback to original body if decoding/parsing fails
            async def original_body_iterator():
                yield body
            response.body_iterator = original_body_iterator()

        return response
