"""
PakLaw AI — Sample Dataset Loader

Uploads and indexes a set of sample Pakistani legal document texts (Statute samples)
to bootstrap local retrieval testing.
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Allow this script to run both from the host and from the Docker backend container.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.extend([str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")])

from app.core.database import AsyncSessionLocal
from app.models.document import Document, DocumentStatus, DocumentType
from app.repositories.document import DocumentRepository
from app.models.user import User

# Sample Pakistan Penal Code sections for grounding
SAMPLE_DATA = [
    {
        "title": "Pakistan Penal Code (Act XLV of 1860) - Selected Sections",
        "description": "Excerpt of Pakistan Penal Code containing general exemptions and private defense rules.",
        "type": DocumentType.ACT,
        "filename": "ppc_excerpt.txt",
        "content": """
THE PAKISTAN PENAL CODE (ACT XLV OF 1860)

Section 96. Things done in private defence:
Nothing is an offence which is done in the exercise of the right of private defence.

Section 97. Right of private defence of the body and of property:
Every person has a right, subject to the restrictions contained in Section 99, to defend:
First. His own body, and the body of any other person, against any offence affecting the human body;
Secondly. The property, whether moveable or immoveable, of himself or of any other person, against any act which is an offence falling under the definition of theft, robbery, mischief or criminal trespass, or which is an attempt to commit theft, robbery, mischief or criminal trespass.

Section 99. Acts against which there is no right of private defence:
There is no right of private defence against an act which does not reasonably cause the apprehension of death or of grievous hurt, if done, or attempted to be done, by a public servant acting in good faith under colour of his office, though that act may not be strictly justifiable by law.
There is no right of private defence in cases in which there is time to have recourse to the protection of the public authorities.
The right of private defence in no case extends to the inflicting of more harm than it is necessary to inflict for the purpose of defence.

Section 100. When the right of private defence of the body extends to causing death:
The right of private defence of the body extends, under the restrictions mentioned in the last preceding section, to the voluntary causing of death or of any other harm to the assailant, if the offence which occasions the exercise of the right be of any of the descriptions hereinafter enumerated, namely:
First. Such an apprehension of death as may reasonably cause the apprehension of death;
Secondly. Such an apprehension of grievous hurt as may reasonably cause the apprehension of grievous hurt;
Thirdly. An assault with the intention of committing rape;
Fourthly. An assault with the intention of gratifying unnatural lust;
Fifthly. An assault with the intention of kidnapping or abducting;
Sixthly. An assault with the intention of wrongfully confining a person.
"""
    }
]


async def load_sample_dataset():
    """Seed sample document and run chunk index splits locally."""
    print("Loading sample legal dataset...")
    
    async with AsyncSessionLocal() as db:
        # Get first user (usually the seeded admin)
        from sqlalchemy import select
        q = select(User).limit(1)
        user = (await db.execute(q)).scalar_one_or_none()
        if not user:
            print("No users found. Please run seed.py first.")
            return

        doc_repo = DocumentRepository(Document, db)

        for item in SAMPLE_DATA:
            # Check duplicate
            existing = await doc_repo.get_by_slug("ppc-excerpt-sample")
            if existing:
                print(f"Sample document '{item['title']}' already exists. Skipping.")
                continue

            doc_id = uuid.uuid4()
            
            # Write content mock file to uploads
            uploads_dir = Path("./uploads")
            uploads_dir.mkdir(parents=True, exist_ok=True)
            mock_path = uploads_dir / f"{doc_id}.txt"
            with open(mock_path, "w", encoding="utf-8") as f:
                f.write(item["content"])

            # Register Doc
            doc_in = {
                "id": doc_id,
                "owner_id": user.id,
                "title": item["title"],
                "slug": "ppc-excerpt-sample",
                "description": item["description"],
                "document_type": item["type"],
                "file_name": item["filename"],
                "file_path": str(mock_path),
                "file_size_bytes": len(item["content"].encode("utf-8")),
                "file_extension": "txt",
                "mime_type": "text/plain",
                "checksum_sha256": uuid.uuid4().hex,  # mock
                "status": DocumentStatus.PENDING,
            }
            document = await doc_repo.create(doc_in)
            
            # Create Job
            job_id = uuid.uuid4()
            job_in = {
                "id": job_id,
                "document_id": doc_id,
                "job_type": "ingestion",
                "status": "queued",
            }
            await doc_repo.create_processing_job(job_in)
            await db.commit()

            # Execute parsing asynchronously in thread pool mimicking worker
            print(f"Triggering background ingestion pipeline task simulator for '{item['title']}'...")
            from workers.tasks.ingestion import process_document_task
            process_document_task.apply(args=[str(doc_id), str(job_id)])

    print("Sample dataset loaded and indexed successfully!")


if __name__ == "__main__":
    asyncio.run(load_sample_dataset())
