"""
PakLaw AI — Document Repository

Handles database operations for Document, DocumentChunk, and ProcessingJob models.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select

from app.models.document import Document, DocumentChunk, ProcessingJob
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Document repository for managing legal documents and chunks."""

    model_class = Document

    async def get_by_slug(self, slug: str) -> Document | None:
        """Fetch a document by its unique slug."""
        query = select(Document).where(Document.slug == slug, not Document.is_deleted)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_checksum(self, checksum: str) -> Document | None:
        """Fetch a document by its file checksum (detect duplicates)."""
        query = select(Document).where(
            Document.checksum_sha256 == checksum, not Document.is_deleted
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_documents(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        user_id: uuid.UUID | None = None,
        document_type: str | None = None,
        is_public: bool | None = None,
        search: str | None = None,
    ) -> tuple[Sequence[Document], int]:
        """Fetch, filter, and paginate documents."""
        query = select(Document).where(not Document.is_deleted)

        # Filters
        if user_id:
            query = query.where(Document.owner_id == user_id)
        if document_type:
            query = query.where(Document.document_type == document_type)
        if is_public is not None:
            query = query.where(Document.is_public == is_public)
        if search:
            query = query.where(
                Document.title.ilike(f"%{search}%") | Document.description.ilike(f"%{search}%")
            )

        # Total count
        from sqlalchemy import func

        count_query = select(func.count(Document.id)).where(not Document.is_deleted)
        if user_id:
            count_query = count_query.where(Document.owner_id == user_id)
        if document_type:
            count_query = count_query.where(Document.document_type == document_type)
        if is_public is not None:
            count_query = count_query.where(Document.is_public == is_public)
        if search:
            count_query = count_query.where(
                Document.title.ilike(f"%{search}%") | Document.description.ilike(f"%{search}%")
            )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Results
        query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    # ── Chunks ────────────────────────────────────────────────
    async def create_chunk(self, chunk_data: dict) -> DocumentChunk:
        """Create a new document chunk."""
        chunk = DocumentChunk(**chunk_data)
        self.db.add(chunk)
        await self.db.flush()
        return chunk

    async def get_chunks_for_document(self, document_id: uuid.UUID) -> Sequence[DocumentChunk]:
        """Fetch all chunks belonging to a document."""
        query = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    # ── Processing Jobs ───────────────────────────────────────
    async def create_processing_job(self, job_data: dict) -> ProcessingJob:
        """Create a new document processing job."""
        job = ProcessingJob(**job_data)
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_processing_job(self, job_id: uuid.UUID) -> ProcessingJob | None:
        """Fetch a processing job by its ID."""
        query = select(ProcessingJob).where(ProcessingJob.id == job_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_job_for_document(self, document_id: uuid.UUID) -> ProcessingJob | None:
        """Fetch the active processing job for a document."""
        query = (
            select(ProcessingJob)
            .where(
                ProcessingJob.document_id == document_id,
                ProcessingJob.status.in_(["queued", "running", "retrying"]),
            )
            .order_by(ProcessingJob.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
