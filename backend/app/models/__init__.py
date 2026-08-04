"""
PakLaw AI — ORM Models Registry Package
Import all models here so SQLAlchemy metadata and mapper registry
are completely aware of all models regardless of import order.
"""

from app.models.audit import AnalyticsEvent, AuditLog
from app.models.conversation import Bookmark, Citation, Conversation, Message
from app.models.document import Document, DocumentChunk, ProcessingJob
from app.models.research import ResearchReport
from app.models.user import Permission, Role, User

__all__ = [
    "User",
    "Role",
    "Permission",
    "Document",
    "DocumentChunk",
    "ProcessingJob",
    "Conversation",
    "Message",
    "Citation",
    "Bookmark",
    "ResearchReport",
    "AuditLog",
    "AnalyticsEvent",
]
