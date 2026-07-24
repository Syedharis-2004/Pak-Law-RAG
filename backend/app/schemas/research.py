"""
PakLaw AI — Research Report Pydantic Schemas
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.research import ExportFormat, ReportStatus


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=5000)
    language: str = Field("en", pattern="^(en|ur|hi|ro)$")
    document_ids: list[uuid.UUID] | None = None
    include_judgments: bool = True
    include_amendments: bool = True
    conversation_id: uuid.UUID | None = None


class LegalIssue(BaseModel):
    issue: str
    relevant_laws: list[str]
    analysis: str


class ApplicableLaw(BaseModel):
    act_title: str
    act_number: str | None
    year: int | None
    relevant_sections: list[str]
    summary: str


class RelevantSection(BaseModel):
    document_title: str
    section_number: str
    section_title: str | None
    content: str
    relevance_reason: str
    citation: str


class ConflictDetected(BaseModel):
    law_a: str
    law_b: str
    conflict_description: str
    recommendation: str


class ReportCitation(BaseModel):
    number: int
    document_title: str
    section: str | None
    page: int | None
    year: int | None


class ResearchReportResponse(BaseModel):
    id: uuid.UUID
    research_query: str
    language: str
    status: ReportStatus
    title: str | None
    executive_summary: str | None
    legal_issues: list[LegalIssue] | None
    applicable_laws: list[ApplicableLaw] | None
    relevant_sections: list[RelevantSection] | None
    conflicts_detected: list[ConflictDetected] | None
    recommendations: list[str] | None
    citations: list[ReportCitation] | None
    full_content_markdown: str | None
    confidence_score: float | None
    documents_searched: int
    sections_retrieved: int
    generation_time_seconds: float | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ResearchListResponse(BaseModel):
    items: list[ResearchReportResponse]
    total: int
    page: int
    page_size: int


class ExportRequest(BaseModel):
    report_id: uuid.UUID
    format: ExportFormat = ExportFormat.PDF
