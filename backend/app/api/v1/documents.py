"""
PakLaw AI — Documents Router

Handles legal document uploading, status polling, downloading, and soft deletion.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile, status
from fastapi.responses import FileResponse

from app.dependencies.auth import PermissionChecker, get_current_user, get_user_repository
from app.models.document import Document, DocumentType
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
    DocumentUpdateRequest,
    DocumentUploadResponse,
)
from app.services.document import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


async def get_document_repository(
    db=Depends(get_user_repository),  # Reuses base repository DB injection
) -> DocumentRepository:
    # Requires active session
    # We resolve DB session locally inside FastAPI dependency
    return DocumentRepository(Document, db.db)


async def get_document_service(
    doc_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> DocumentService:
    return DocumentService(doc_repo)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("documents", "upload"))],
)
async def upload_document(
    file: UploadFile,
    document_type: DocumentType = Form(DocumentType.OTHER),
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """Upload a new legal document for background parsing, OCR, and embedding."""
    return await doc_service.upload_document(file, current_user.id, document_type)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    document_type: str | None = None,
    is_public: bool | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """Retrieve document directory listings with metadata filters."""
    # Regular users only see public documents, admins see all. Scoped if filter applied.
    user_id_scope = None if current_user.is_superuser else current_user.id
    public_scope = is_public if current_user.is_superuser else True

    return await doc_service.list_documents(
        page=page,
        page_size=page_size,
        user_id=user_id_scope,
        document_type=document_type,
        is_public=public_scope,
        search=search,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    doc_service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    """Retrieve metadata of a specific legal document."""
    return await doc_service.get_document(document_id)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    doc_service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the pipeline processing status and OCR progress for a document."""
    return await doc_service.get_document_status(document_id)


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """Download a public source file, or a private file owned by the caller."""
    doc = await doc_service.get_document_file(document_id)
    if not doc.is_public and doc.owner_id != current_user.id and not current_user.is_superuser:
        from app.core.exceptions import AuthorizationError

        raise AuthorizationError("Cannot download documents owned by other users")
    return FileResponse(path=doc.file_path, media_type=doc.mime_type, filename=doc.file_name)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    schema: DocumentUpdateRequest,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """Update metadata properties of an indexed legal document."""
    # Superusers can edit any, regular users edit their own
    doc = await doc_service.get_document(document_id)
    if doc.owner_id != current_user.id and not current_user.is_superuser:
        from app.core.exceptions import AuthorizationError

        raise AuthorizationError("Cannot update documents owned by other users")

    return await doc_service.update_document(document_id, schema)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
):
    """Soft delete a document and purge all associated vector indexing points."""
    doc = await doc_service.get_document(document_id)
    if doc.owner_id != current_user.id and not current_user.is_superuser:
        from app.core.exceptions import AuthorizationError

        raise AuthorizationError("Cannot delete documents owned by other users")

    await doc_service.delete_document(document_id)
