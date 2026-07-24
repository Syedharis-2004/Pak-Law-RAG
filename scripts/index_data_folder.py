"""
PakLaw AI — Data Folder Indexer Script

Registers and indexes all PDF files in the workspace 'data/' folder
into the PostgreSQL database and Qdrant vector database.
"""

import asyncio
import hashlib
import os
import shutil
import sys
import uuid
from pathlib import Path
from slugify import slugify

# Allow this script to run both from the host and from the Docker backend container.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.extend([str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")])

from app.core.database import AsyncSessionLocal
from app.models.audit import AnalyticsEvent, AuditLog
from app.models.conversation import Bookmark, Citation, Conversation, Message
from app.models.document import Document, DocumentChunk, DocumentStatus, DocumentType, ProcessingJob
from app.models.research import ResearchReport
from app.models.user import Permission, Role, User
from app.repositories.document import DocumentRepository
from app.repositories.mongodb_repo import MongoDBRepository
from ai.pipelines.ingestion import IngestionPipeline


def get_doc_type(filename: str) -> DocumentType:
    """Map filename to appropriate DocumentType."""
    lower_fn = filename.lower()
    if "act" in lower_fn or "relief" in lower_fn or "procedure" in lower_fn or "penal" in lower_fn or "shahadat" in lower_fn:
        return DocumentType.ACT
    elif "ordinance" in lower_fn or "tax" in lower_fn:
        return DocumentType.ORDINANCE
    elif "constitution" in lower_fn:
        return DocumentType.CONSTITUTION
    elif "rules" in lower_fn:
        return DocumentType.RULES
    elif "regulation" in lower_fn:
        return DocumentType.REGULATION
    elif "judgment" in lower_fn:
        return DocumentType.JUDGMENT
    elif "contract" in lower_fn:
        return DocumentType.CONTRACT
    else:
        return DocumentType.OTHER


def get_clean_title(filename: str) -> str:
    """Format file name to a nice title."""
    name_without_ext = filename.rsplit(".", 1)[0]
    cleaned = name_without_ext.replace("-", " ").replace("_", " ")
    return cleaned.title()


async def index_data_folder():
    """Scan 'data' folder and ingest all PDFs into the system."""
    data_dir = Path("data")
    from app.core.config import settings

    uploads_dir = Path(settings.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    if not data_dir.exists():
        print("Error: 'data/' directory not found in the workspace root.")
        return

    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in 'data/' directory.")
        return

    print(f"Found {len(pdf_files)} PDF documents to process.")

    async with AsyncSessionLocal() as db:
        # Resolve seeded user/admin to assign documents
        from sqlalchemy import select
        q = select(User).limit(1)
        user = (await db.execute(q)).scalar_one_or_none()
        if not user:
            print("Error: No users found. Please run seed.py first.")
            return

        doc_repo = DocumentRepository(Document, db)
        pipeline = IngestionPipeline()

        for pdf_path in pdf_files:
            filename = pdf_path.name
            title = get_clean_title(filename)
            doc_type = get_doc_type(filename)

            print(f"\n--------------------------------------------------")
            print(f"Processing: '{filename}' -> Title: '{title}' ({doc_type.value})")

            # 1. Compute checksum and file size
            with open(pdf_path, "rb") as f:
                content = f.read()
            
            file_size = len(content)
            checksum = hashlib.sha256(content).hexdigest()

            # 2. Check duplicates
            existing = await doc_repo.get_by_checksum(checksum)
            if existing:
                print(f"Skipping: Document with identical checksum already exists (ID: {existing.id}, Title: {existing.title})")
                continue

            doc_id = uuid.uuid4()
            dest_filename = f"{doc_id}.pdf"
            dest_path = uploads_dir / dest_filename

            # 3. Copy file to uploads folder
            shutil.copy2(pdf_path, dest_path)
            print(f"Copied to uploads: {dest_path}")

            # 4. Generate slug
            base_slug = slugify(title)
            slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

            # 5. Register Document metadata in PostgreSQL
            doc_in = {
                "id": doc_id,
                "owner_id": user.id,
                "title": title,
                "slug": slug,
                "document_type": doc_type,
                "file_name": filename,
                "file_path": str(dest_path),
                "file_size_bytes": file_size,
                "file_extension": "pdf",
                "mime_type": "application/pdf",
                "checksum_sha256": checksum,
                "status": DocumentStatus.PENDING,
            }
            await doc_repo.create(doc_in)

            # 6. Register Ingestion Processing Job
            job_id = uuid.uuid4()
            job_in = {
                "id": job_id,
                "document_id": doc_id,
                "job_type": "ingestion",
                "status": "queued",
            }
            await doc_repo.create_processing_job(job_in)
            await db.commit()

            # Dual sync metadata to MongoDB
            await MongoDBRepository.sync_document(doc_in)
            await MongoDBRepository.sync_job(job_in)
            print(f"Registered document in DB & MongoDB (Doc ID: {doc_id}, Job ID: {job_id})")

            # 7. Execute ingestion pipeline synchronously
            print(f"Extracting, chunking, embedding, and indexing in Qdrant...")
            try:
                await pipeline.ingest_document(str(doc_id), str(job_id))
                print(f"Successfully finished ingestion for '{title}'!")
            except Exception as e:
                print(f"Error during ingestion of '{title}': {str(e)}")

    print("\n--------------------------------------------------")
    print("Completed indexing data folder.")


if __name__ == "__main__":
    asyncio.run(index_data_folder())
