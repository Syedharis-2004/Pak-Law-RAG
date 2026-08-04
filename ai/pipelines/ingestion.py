"""
PakLaw AI — Document Ingestion Pipeline

Extracts text from various file formats (using PaddleOCR for scanned pages),
performs semantic chunking, embeds text using BGE-M3 (dense & sparse),
and stores vectors in Qdrant and chunks metadata in PostgreSQL.
"""

import uuid
from datetime import datetime, timezone

import pdf2image
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.document import Document, DocumentStatus
from app.repositories.document import DocumentRepository
from app.repositories.mongodb_repo import MongoDBRepository
from docx import Document as DocxDocument
from pypdf import PdfReader
from qdrant_client.http import models as qdrant_models

from ai.embeddings.bge_m3 import BGEM3Embedding
from ai.ocr.paddleocr_engine import OCRProcessor
from ai.qdrant.collections import QdrantCollectionManager
from ai.utils.text_cleaning import clean_text, extract_sections_from_text


class IngestionPipeline:
    """Ingests file formats, runs OCR, chunks content, generates embeddings, and indexes them."""

    def __init__(self) -> None:
        self.embed_model = BGEM3Embedding()
        self.ocr_processor = OCRProcessor()
        self.qdrant_manager = QdrantCollectionManager()

    async def ingest_document(self, document_id: str, job_id: str) -> None:
        """Runs the complete ingestion pipeline for a document."""
        async with AsyncSessionLocal() as db:
            doc_repo = DocumentRepository(Document, db)
            doc = await doc_repo.get(uuid.UUID(document_id))
            job = await doc_repo.get_processing_job(uuid.UUID(job_id))

            if not doc or not job:
                return

            try:
                # Update status to processing
                doc.status = DocumentStatus.PROCESSING
                doc.processing_started_at = datetime.now(timezone.utc)
                job.status = "running"
                job.started_at = datetime.now(timezone.utc)
                job.progress_percent = 10
                job.progress_message = "Extracting text from file..."
                await db.commit()

                # Extract Text
                file_ext = doc.file_extension.lower()
                extracted_text = ""
                ocr_needed = False
                pages_data = []

                if file_ext == "pdf":
                    pages_data, ocr_needed = self._extract_pdf_content(doc.file_path)
                elif file_ext == "docx":
                    extracted_text = self._extract_docx_content(doc.file_path)
                    pages_data = [{"page_num": 1, "text": extracted_text}]
                elif file_ext in ("txt", "md", "html"):
                    with open(doc.file_path, "r", encoding="utf-8") as f:
                        extracted_text = f.read()
                    pages_data = [{"page_num": 1, "text": extracted_text}]
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}")

                # Run OCR if needed
                if ocr_needed and file_ext == "pdf":
                    job.progress_message = "Scanned PDF detected. Running PaddleOCR..."
                    job.progress_percent = 30
                    await db.commit()
                    pages_data = self._ocr_pdf_pages(doc.file_path)
                    doc.ocr_confidence = (
                        sum(p["confidence"] for p in pages_data) / len(pages_data)
                        if pages_data
                        else 0.0
                    )

                # Clean text
                for p in pages_data:
                    p["text"] = clean_text(p["text"])

                # Update metadata status
                doc.total_pages = len(pages_data)
                job.progress_message = "Segmenting text into semantic chunks..."
                job.progress_percent = 50
                await db.commit()

                # Semantic Chunking
                chunks = self._chunk_pages(pages_data)
                doc.total_chunks = len(chunks)

                # Generate Embeddings & Index in Qdrant
                job.progress_message = "Generating BGE-M3 embeddings & indexing..."
                job.progress_percent = 70
                await db.commit()

                # A single collection keeps cross-statute search complete. The document type
                # remains in the payload and is used as a filter at retrieval time.
                collection_name = "legal_documents"

                self.qdrant_manager.create_collection_if_not_exists(collection_name)
                doc.qdrant_collection = collection_name

                # Process batch embeddings
                points = []
                for idx, chunk in enumerate(chunks):
                    # Generate dense and sparse vectors
                    dense_vector = self.embed_model.get_text_embedding(chunk["content"])
                    sparse_vector = self.embed_model.get_sparse_embedding(
                        chunk["content"]
                    )

                    point_id = str(uuid.uuid4())

                    # Create payload
                    payload = {
                        "document_id": str(doc.id),
                        "chunk_id": point_id,
                        "title": doc.title,
                        "document_type": doc.document_type.value,
                        "jurisdiction": doc.jurisdiction,
                        "year": doc.year,
                        "language": doc.language,
                        "page_number": chunk["page_number"],
                        "section_number": chunk.get("section_number"),
                        "section_title": chunk.get("section_title"),
                        "text": chunk["content"],
                    }

                    # Prepare Qdrant Point
                    points.append(
                        qdrant_models.PointStruct(
                            id=point_id,
                            vector={
                                "": dense_vector,
                                "sparse-text": qdrant_models.SparseVector(
                                    indices=list(sparse_vector.keys()),
                                    values=list(sparse_vector.values()),
                                ),
                            },
                            payload=payload,
                        )
                    )

                    # Save Chunk to SQL DB & MongoDB
                    chunk_db_in = {
                        "id": uuid.UUID(point_id),
                        "document_id": doc.id,
                        "chunk_index": idx,
                        "page_number": chunk["page_number"],
                        "content": chunk["content"],
                        "section_number": chunk.get("section_number"),
                        "section_title": chunk.get("section_title"),
                        "qdrant_point_id": point_id,
                        "token_count": len(chunk["content"].split()),  # Simple proxy
                        "char_count": len(chunk["content"]),
                    }
                    await doc_repo.create_chunk(chunk_db_in)
                    await MongoDBRepository.sync_chunk(chunk_db_in)

                # Upsert points to Qdrant
                if points:
                    self.qdrant_manager.client.upsert(
                        collection_name=collection_name, points=points
                    )

                # Finalize Job & Document Status
                doc.status = DocumentStatus.READY
                doc.processing_completed_at = datetime.now(timezone.utc)
                job.status = "completed"
                job.completed_at = datetime.now(timezone.utc)
                job.progress_percent = 100
                job.progress_message = "Ingestion completed successfully."
                await db.commit()

                # Dual sync completed document & job to MongoDB
                doc_dict = {
                    "id": doc.id,
                    "owner_id": doc.owner_id,
                    "title": doc.title,
                    "slug": doc.slug,
                    "document_type": doc.document_type.value,
                    "file_name": doc.file_name,
                    "file_path": doc.file_path,
                    "file_size_bytes": doc.file_size_bytes,
                    "file_extension": doc.file_extension,
                    "mime_type": doc.mime_type,
                    "checksum_sha256": doc.checksum_sha256,
                    "status": doc.status.value,
                    "total_pages": doc.total_pages,
                    "total_chunks": doc.total_chunks,
                    "qdrant_collection": doc.qdrant_collection,
                    "ocr_confidence": doc.ocr_confidence,
                    "jurisdiction": doc.jurisdiction,
                    "year": doc.year,
                    "language": doc.language,
                }
                await MongoDBRepository.sync_document(doc_dict)
                await MongoDBRepository.sync_job(
                    {
                        "id": job.id,
                        "document_id": doc.id,
                        "status": job.status,
                        "progress_percent": job.progress_percent,
                        "progress_message": job.progress_message,
                        "completed_at": job.completed_at,
                    }
                )

            except Exception as e:
                import traceback

                error_trace = traceback.format_exc()
                doc.status = DocumentStatus.FAILED
                doc.processing_error = str(e)
                job.status = "failed"
                job.error_message = str(e)
                job.error_traceback = error_trace
                await db.commit()
                raise

    def _extract_pdf_content(self, file_path: str) -> tuple[list[dict], bool]:
        """Extract pages from standard PDF. Flags if PDF seems scanned."""
        reader = PdfReader(file_path)
        pages_data = []
        total_chars = 0

        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            total_chars += len(text.strip())
            pages_data.append({"page_num": idx + 1, "text": text})

        # Heuristic: If average character count per page is very low, it's likely scanned
        avg_chars = total_chars / len(reader.pages) if reader.pages else 0
        ocr_needed = avg_chars < 150

        return pages_data, ocr_needed

    def _extract_docx_content(self, file_path: str) -> str:
        """Extract text from Word Document."""
        doc = DocxDocument(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    def _ocr_pdf_pages(self, file_path: str) -> list[dict]:
        """Convert PDF pages to images and run PaddleOCR."""
        pages_data = []
        try:
            # Convert PDF pages to PIL Images
            images = pdf2image.convert_from_path(file_path, dpi=150)
            for idx, img in enumerate(images):
                text, confidence = self.ocr_processor.extract_text_from_pdf_page(img)
                pages_data.append(
                    {"page_num": idx + 1, "text": text, "confidence": confidence}
                )
        except Exception as e:
            raise RuntimeError(f"Failed converting or OCRing PDF: {e!s}")
        return pages_data

    def _chunk_pages(self, pages_data: list[dict]) -> list[dict]:
        """Chunks texts using a sentence splitter strategy preserving section scope."""
        chunks = []
        # Simple sliding window chunker scoped per page/sections
        for page in pages_data:
            page_text = page["text"]
            page_num = page["page_num"]

            # Try to identify sections within the page
            sections = extract_sections_from_text(page_text)
            if not sections:
                # If no section headings detected, divide page into sliding chunks
                words = page_text.split()
                chunk_size = settings.CHUNK_SIZE
                overlap = settings.CHUNK_OVERLAP

                i = 0
                while i < len(words):
                    chunk_words = words[i : i + chunk_size]
                    chunk_text = " ".join(chunk_words)
                    chunks.append(
                        {
                            "page_number": page_num,
                            "content": chunk_text,
                            "section_number": None,
                            "section_title": None,
                        }
                    )
                    i += chunk_size - overlap
            else:
                for sec in sections:
                    chunks.append(
                        {
                            "page_number": page_num,
                            "content": sec["content"],
                            "section_number": sec["section_number"],
                            "section_title": sec["section_title"],
                        }
                    )

        return chunks
