"""
PakLaw AI — Document Pydantic Schemas
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.document import DocumentStatus, DocumentType


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    title: str
    file_name: str
    file_size_bytes: int
    status: DocumentStatus
    document_type: DocumentType
    job_id: uuid.UUID
    message: str

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    document_type: DocumentType
    jurisdiction: str | None
    subject: str | None
    act_number: str | None
    year: int | None
    language: str
    file_name: str
    file_size_bytes: int
    file_extension: str
    status: DocumentStatus
    total_pages: int | None
    total_chunks: int
    is_public: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentUpdateRequest(BaseModel):
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    document_type: DocumentType | None = None
    jurisdiction: str | None = Field(None, max_length=100)
    subject: str | None = Field(None, max_length=200)
    act_number: str | None = Field(None, max_length=100)
    year: int | None = Field(None, ge=1800, le=2100)
    is_public: bool | None = None


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: DocumentStatus
    processing_error: str | None
    total_chunks: int
    progress_percent: int
    progress_message: str | None
    job_id: uuid.UUID | None
    started_at: datetime | None
    completed_at: datetime | None


class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    page_number: int | None
    content: str
    section_title: str | None
    section_number: str | None
    token_count: int

    model_config = {"from_attributes": True}
