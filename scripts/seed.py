"""
PakLaw AI — Database Seeding Script

Creates default system roles, permission mapping matrix, and registers the initial
Administrator superuser account.
"""

import asyncio
import sys
from pathlib import Path

# Allow this script to run both from the host and from the Docker backend container.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.extend([str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")])

from app.core.database import AsyncSessionLocal
from app.models.audit import AnalyticsEvent, AuditLog
from app.models.conversation import Bookmark, Citation, Conversation, Message
from app.models.document import Document, DocumentChunk, ProcessingJob
from app.models.research import ResearchReport
from app.models.user import Permission, Role, User
from app.core.security import hash_password
from app.core.logging_config import configure_logging, get_logger
from app.core.mongodb import mongodb_manager
from app.repositories.mongodb_repo import MongoDBRepository

configure_logging()
logger = get_logger("seeder")

# System permissions to generate
PERMISSIONS = [
    # Document permissions
    ("documents", "upload", "Upload files for OCR/indexing"),
    ("documents", "delete", "Delete indexing nodes and source files"),
    ("documents", "edit", "Modify document classification metadata"),
    
    # System settings
    ("admin", "users:manage", "Deactivate accounts or reassign roles"),
    ("admin", "analytics:view", "Inspect metrics and platform resource footprint"),
]

# Roles matrix mapping permissions
ROLES_MATRIX = {
    "admin": [
        "documents:upload",
        "documents:delete",
        "documents:edit",
        "admin:users:manage",
        "admin:analytics:view",
    ],
    "lawyer": [
        "documents:upload",
        "documents:edit",
    ],
    "citizen": [
        # Citizens only read indices
    ],
}


async def seed_database():
    """Initializes tables, seeds RBAC roles/permissions, and registers default admin."""
    logger.info("Connecting to target database for seeding...")
    from app.core.database import create_tables
    await create_tables()
    
    async with AsyncSessionLocal() as db:
        # 1. Create Permissions
        logger.info("Creating granular system permissions...")
        db_perms = {}
        for res, act, desc in PERMISSIONS:
            name = f"{res}:{act}"
            # Check existing
            from sqlalchemy import select
            q = select(Permission).where(Permission.name == name)
            existing = (await db.execute(q)).scalar_one_or_none()
            if not existing:
                perm = Permission(name=name, resource=res, action=act, description=desc)
                db.add(perm)
                db_perms[name] = perm
            else:
                db_perms[name] = existing
        await db.flush()

        # 2. Create Roles and Assign Permissions
        logger.info("Initializing system roles & mapping RBAC matrix...")
        from sqlalchemy.orm import selectinload
        db_roles = {}
        for role_name, allowed_perms in ROLES_MATRIX.items():
            q = select(Role).options(selectinload(Role.permissions)).where(Role.name == role_name)
            role = (await db.execute(q)).scalar_one_or_none()
            if not role:
                role = Role(
                    name=role_name,
                    display_name=role_name.capitalize(),
                    description=f"Default system {role_name} role.",
                    is_system=True,
                )
                db.add(role)
            
            # Map permissions
            role.permissions = [db_perms[p] for p in allowed_perms if p in db_perms]
            db_roles[role_name] = role
        await db.flush()

        # 3. Create Default Superuser
        logger.info("Registering default system administrator...")
        admin_email = "admin@paklaw.ai"
        q = select(User).options(selectinload(User.roles)).where(User.email == admin_email)
        admin_user = (await db.execute(q)).scalar_one_or_none()
        
        if not admin_user:
            admin_user = User(
                email=admin_email,
                hashed_password=hash_password("PakLawAdmin2026!"),
                full_name="PakLaw Admin",
                is_active=True,
                is_verified=True,
                is_superuser=True,
            )
            db.add(admin_user)
            # Link admin role
            admin_user.roles.append(db_roles["admin"])
            logger.info(f"Admin registered successfully with email: {admin_email}")
        else:
            logger.info("Admin account already registered. Skipping creation.")

        await db.commit()
        
        # Initialize MongoDB indexes and sync admin user
        await mongodb_manager.init_indexes()
        await MongoDBRepository.sync_user({
            "id": admin_user.id,
            "email": admin_user.email,
            "full_name": admin_user.full_name,
            "is_active": admin_user.is_active,
            "is_verified": admin_user.is_verified,
            "is_superuser": admin_user.is_superuser,
            "roles": ["admin"],
        })
        logger.info("Database & MongoDB seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
