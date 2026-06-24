from typing import Any

from pydantic import RootModel


class SettingsPayload(RootModel[dict[str, Any]]):
    pass
