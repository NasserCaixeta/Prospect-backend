from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=120)
    role: UserRole = UserRole.USER


class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
