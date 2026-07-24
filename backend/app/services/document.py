"""
PakLaw AI — Document Service

Handles document uploading, local storage management, checksum verification,
deleting, metadata updating, and queuing the ingestion Celery task.
"""

import hashlib
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from slugify import slugify

from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from app.models.document import Document, DocumentStatus, DocumentType
from app.repositories.document import DocumentRepository
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
    DocumentUpdateRequest,
    DocumentUploadResponse,
)


class DocumentService:
    """Service layer for document management and processing ingestion."""

    def __init__(self, doc_repo: DocumentRepository) -> None:
        self.doc_repo = doc_repo

    async def upload_document(
        self, file: UploadFile, owner_id: uuid.UUID, document_type: DocumentType
    ) -> DocumentUploadResponse:
        """
        Upload file, save to local disk, compute checksum to prevent duplicates,
        save metadata to DB, and queue background ingestion task.
        """
        # Validate extension
        ext = file.filename.split(".")[-1].lower() if file.filename else ""
        if ext not in settings.allowed_extensions_list:
            raise UnsupportedFileTypeError(ext)

        # Read content and compute hash
        content = await file.read()
        file_size = len(content)

        # Validate size
        max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise FileTooLargeError(settings.MAX_UPLOAD_SIZE_MB)

        checksum = hashlib.sha256(content).hexdigest()

        # Check for duplicate
        existing_doc = await self.doc_repo.get_by_checksum(checksum)
        if existing_doc:
            raise ConflictError(
                f"Document already exists with title '{existing_doc.title}'"
            )

        # Create upload directory
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        doc_id = uuid.uuid4()
        file_name = f"{doc_id}.{ext}"
        file_path = upload_dir / file_name

        # Save to disk
        with open(file_path, "wb") as f:
            f.write(content)

        # Set title and slug
        original_filename = file.filename or "untitled"
        title = original_filename.rsplit(".", 1)[0]
        base_slug = slugify(title)
        slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

        # Create document DB record
        doc_in = {
            "id": doc_id,
            "owner_id": owner_id,
            "title": title,
            "slug": slug,
            "document_type": document_type,
            "file_name": original_filename,
            "file_path": str(file_path),
            "file_size_bytes": file_size,
            "file_extension": ext,
            "mime_type": file.content_type or "application/octet-stream",
            "checksum_sha256": checksum,
            "status": DocumentStatus.PENDING,
        }
        document = await self.doc_repo.create(doc_in)

        # Create processing job record
        job_id = uuid.uuid4()
        job_in = {
            "id": job_id,
            "document_id": doc_id,
            "job_type": "ingestion",
            "status": "queued",
        }
        await self.doc_repo.create_processing_job(job_in)

        # The worker runs in a different database session, so make the document and
        # job visible before publishing its Celery task.
        await self.doc_repo.db.commit()

        # Trigger background Celery worker task
        from workers.tasks.ingestion import process_document_task
        task = process_document_task.delay(str(doc_id), str(job_id))
        
        # Save celery task ID
        job = await self.doc_repo.get_processing_job(job_id)
        if job:
            job.celery_task_id = task.id
            await self.doc_repo.db.flush()

        return DocumentUploadResponse(
            id=doc_id,
            title=title,
            file_name=original_filename,
            file_size_bytes=file_size,
            status=DocumentStatus.PENDING,
            document_type=document_type,
            job_id=job_id,
            message="Document uploaded successfully. Processing started in background.",
        )

    async def get_document(self, doc_id: uuid.UUID) -> DocumentResponse:
        """Fetch document details."""
        doc = await self.doc_repo.get(doc_id)
        if not doc or doc.is_deleted:
            raise NotFoundError("Document", str(doc_id))
        return DocumentResponse.from_orm(doc)

    async def get_document_file(self, doc_id: uuid.UUID) -> Document:
        """Return an existing source document for an authorized download route."""
        doc = await self.doc_repo.get(doc_id)
        if not doc or doc.is_deleted:
            raise NotFoundError("Document", str(doc_id))
        if not os.path.isfile(doc.file_path):
            raise NotFoundError("Document file", str(doc_id))
        return doc

    async def get_document_status(self, doc_id: uuid.UUID) -> DocumentStatusResponse:
        """Fetch processing status and progress percentage."""
        doc = await self.doc_repo.get(doc_id)
        if not doc or doc.is_deleted:
            raise NotFoundError("Document", str(doc_id))

        active_job = await self.doc_repo.get_active_job_for_document(doc_id)

        return DocumentStatusResponse(
            id=doc_id,
            title=doc.title,
            status=doc.status,
            processing_error=doc.processing_error,
            total_chunks=doc.total_chunks,
            progress_percent=active_job.progress_percent if active_job else 100 if doc.status == DocumentStatus.READY else 0,
            progress_message=active_job.progress_message if active_job else None,
            job_id=active_job.id if active_job else None,
            started_at=active_job.started_at if active_job else None,
            completed_at=active_job.completed_at if active_job else None,
        )

    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: uuid.UUID | None = None,
        document_type: str | None = None,
        is_public: bool | None = None,
        search: str | None = None,
    ) -> DocumentListResponse:
        """List and paginate documents with filters."""
        skip = (page - 1) * page_size
        docs, total = await self.doc_repo.get_documents(
            skip=skip,
            limit=page_size,
            user_id=user_id,
            document_type=document_type,
            is_public=is_public,
            search=search,
        )

        items = [DocumentResponse.from_orm(d) for d in docs]
        import math
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return DocumentListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_document(
        self, doc_id: uuid.UUID, schema: DocumentUpdateRequest
    ) -> DocumentResponse:
        """Update document metadata fields."""
        doc = await self.doc_repo.get(doc_id)
        if not doc or doc.is_deleted:
            raise NotFoundError("Document", str(doc_id))

        updated_data = schema.model_dump(exclude_unset=True)
        updated_doc = await self.doc_repo.update(doc, updated_data)
        return DocumentResponse.from_orm(updated_doc)

    async def delete_document(self, doc_id: uuid.UUID) -> None:
        """Soft delete a document from database and delete from Qdrant vector store."""
        doc = await self.doc_repo.get(doc_id)
        if not doc or doc.is_deleted:
            raise NotFoundError("Document", str(doc_id))

        # Soft delete in DB
        from datetime import datetime, timezone
        doc.is_deleted = True
        doc.deleted_at = datetime.now(timezone.utc)
        doc.status = DocumentStatus.DELETED
        await self.doc_repo.db.flush()

        # Delete local file if it exists
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception:
                pass  # Avoid blocking if file deletion fails

        # Trigger background task to delete from Qdrant vector store
        from workers.tasks.ingestion import delete_document_vector_task
        delete_document_vector_task.delay(str(doc_id))
