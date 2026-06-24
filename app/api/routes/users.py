from fastapi import APIRouter, status

from app.api.deps import AdminUser, DbSession
from app.schemas.user import UserCreate, UserRead
from app.services.users import create_user, list_users

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_internal_user(payload: UserCreate, db: DbSession, _: AdminUser) -> UserRead:
    return create_user(
        db,
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=payload.role,
    )


@router.get("", response_model=list[UserRead])
def list_internal_users(db: DbSession, _: AdminUser) -> list[UserRead]:
    return list_users(db)
