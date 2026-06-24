from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.setting import Setting


def get_settings_map(db: Session) -> dict[str, Any]:
    rows = db.scalars(select(Setting).order_by(Setting.key))
    return {row.key: row.value for row in rows}


def patch_settings(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    for key, value in payload.items():
        setting = db.scalar(select(Setting).where(Setting.key == key))
        if setting is None:
            setting = Setting(key=key, value=value)
            db.add(setting)
        else:
            setting.value = value
    db.commit()
    return get_settings_map(db)
