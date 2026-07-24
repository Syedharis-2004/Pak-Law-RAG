"""
PakLaw AI — Admin Operations Router

Handles user role management, system analytics audits, and document control.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_active_superuser, get_user_repository
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/admin", tags=["System Administration"])


@router.get(
    "/users",
    response_model=list[UserResponse],
    dependencies=[Depends(get_current_active_superuser)],
)
async def admin_list_users(
    page: int = 1,
    page_size: int = 50,
    search: str | None = None,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """List users registered on the platform with pagination and search."""
    skip = (page - 1) * page_size
    users, _ = await user_repo.get_users_list(skip=skip, limit=page_size, search=search)
    return [UserResponse.from_orm_with_roles(u) for u in users]


@router.put(
    "/users/{user_id}/roles",
    response_model=UserResponse,
    dependencies=[Depends(get_current_active_superuser)],
)
async def admin_assign_roles(
    user_id: uuid.UUID,
    roles: list[str],
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Modify roles assigned to a user (RBAC management)."""
    user = await user_repo.get_with_roles(user_id)
    if not user:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User", str(user_id))

    # Clear current roles
    user.roles = []
    
    # Resolve and assign new roles
    for role_name in roles:
        role = await user_repo.get_role_by_name(role_name)
        if role:
            user.roles.append(role)

    await user_repo.db.flush()
    return UserResponse.from_orm_with_roles(user)


@router.get(
    "/analytics/summary",
    dependencies=[Depends(get_current_active_superuser)],
)
async def admin_get_analytics(
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Retrieve platform usage analytics including storage and query volumes."""
    # Run basic summary queries
    from sqlalchemy import select, func
    from app.models.user import User as User_Model
    from app.models.document import Document as Doc_Model
    from app.models.conversation import Message as Msg_Model

    user_count_q = select(func.count(User_Model.id)).where(User_Model.is_deleted == False)
    doc_count_q = select(func.count(Doc_Model.id)).where(Doc_Model.is_deleted == False)
    msg_count_q = select(func.count(Msg_Model.id))
    storage_sum_q = select(func.sum(Doc_Model.file_size_bytes)).where(Doc_Model.is_deleted == False)

    users_total = (await user_repo.db.execute(user_count_q)).scalar_one()
    docs_total = (await user_repo.db.execute(doc_count_q)).scalar_one()
    msgs_total = (await user_repo.db.execute(msg_count_q)).scalar_one()
    storage_total = (await user_repo.db.execute(storage_sum_q)).scalar_one() or 0

    return {
        "stats": {
            "total_users": users_total,
            "total_documents": docs_total,
            "total_ai_messages": msgs_total,
            "total_storage_used_mb": round(storage_total / (1024 * 1024), 2),
        }
    }
