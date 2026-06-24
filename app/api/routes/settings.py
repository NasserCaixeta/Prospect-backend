from typing import Any

from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.services.settings import get_settings_map, patch_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings_route(db: DbSession, _: CurrentUser) -> dict[str, Any]:
    return get_settings_map(db)


@router.patch("")
def patch_settings_route(payload: dict[str, Any], db: DbSession, _: AdminUser) -> dict[str, Any]:
    return patch_settings(db, payload)
