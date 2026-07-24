"""
PakLaw AI — Legal Research Report Service

Orchestrates multi-step legal research workflows and generates
structured reports in PDF, DOCX, or Markdown formats.
"""

import uuid
from datetime import datetime, timezone

from app.core.exceptions import NotFoundError
from app.models.research import ReportStatus, ResearchReport
from app.repositories.research import ResearchRepository
from app.schemas.research import (
    ExportFormat,
    ResearchListResponse,
    ResearchRequest,
    ResearchReportResponse,
)


class ResearchService:
    """Service layer for managing AI Legal Research Reports."""

    def __init__(self, research_repo: ResearchRepository) -> None:
        self.research_repo = research_repo

    async def create_research_report(
        self, request: ResearchRequest, user_id: uuid.UUID
    ) -> ResearchReportResponse:
        """
        Creates a research report record in queued status and triggers
        the async Celery research workflow.
        """
        report_id = uuid.uuid4()

        # Create report record
        report_in = {
            "id": report_id,
            "user_id": user_id,
            "conversation_id": request.conversation_id,
            "research_query": request.query,
            "language": request.language,
            "status": ReportStatus.QUEUED,
        }
        report = await self.research_repo.create(report_in)
        await self.research_repo.db.commit()

        # Trigger background Celery task
        from workers.tasks.report import generate_research_report_task
        generate_research_report_task.delay(
            str(report_id),
            request.query,
            request.language,
            [str(d) for d in request.document_ids] if request.document_ids else None,
            request.include_judgments,
            request.include_amendments,
        )

        return ResearchReportResponse.from_orm(report)

    async def get_report(self, report_id: uuid.UUID, user_id: uuid.UUID) -> ResearchReportResponse:
        """Fetch a specific research report."""
        report = await self.research_repo.get(report_id)
        if not report or report.is_deleted or report.user_id != user_id:
            raise NotFoundError("ResearchReport", str(report_id))
        return ResearchReportResponse.from_orm(report)

    async def list_reports(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 10
    ) -> ResearchListResponse:
        """List and paginate user's research reports."""
        skip = (page - 1) * page_size
        reports, total = await self.research_repo.get_user_reports(
            user_id, skip=skip, limit=page_size
        )
        items = [ResearchReportResponse.from_orm(r) for r in reports]
        return ResearchListResponse(
            items=items, total=total, page=page, page_size=page_size
        )

    async def delete_report(self, report_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Soft delete a research report."""
        report = await self.research_repo.get(report_id)
        if not report or report.is_deleted or report.user_id != user_id:
            raise NotFoundError("ResearchReport", str(report_id))
        report.is_deleted = True
        await self.research_repo.db.flush()

    async def export_report(
        self, report_id: uuid.UUID, export_format: ExportFormat, user_id: uuid.UUID
    ) -> str:
        """
        Return the file path of the exported report (PDF/DOCX).
        If the file is not yet generated, it builds it on demand.
        """
        report = await self.research_repo.get(report_id)
        if not report or report.is_deleted or report.user_id != user_id:
            raise NotFoundError("ResearchReport", str(report_id))

        if report.status != ReportStatus.COMPLETED:
            raise ValueError("Report is not completed yet.")

        if export_format == ExportFormat.PDF:
            if report.pdf_path:
                return report.pdf_path
            # Generate PDF on demand
            from ai.utils.pdf_generator import generate_pdf_report
            pdf_path = generate_pdf_report(report)
            report.pdf_path = pdf_path
            await self.research_repo.db.flush()
            return pdf_path

        elif export_format == ExportFormat.DOCX:
            if report.docx_path:
                return report.docx_path
            # Generate DOCX on demand
            from ai.utils.docx_generator import generate_docx_report
            docx_path = generate_docx_report(report)
            report.docx_path = docx_path
            await self.research_repo.db.flush()
            return docx_path

        else:
            raise ValueError(f"Export format '{export_format}' is not supported.")
