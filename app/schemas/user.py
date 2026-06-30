from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.enums.user import UserRole


class UserBase(BaseModel):
    email: EmailStr = Field(max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(min_length=8, max_length=128, default=None)
    avatar_url: str | None = None


class UserUpdateSelf(BaseModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    avatar_url: str | None = None


class UpdatePassword(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = Field(default=UserRole.BUYER)


class UserRespond(UserBase):
    id: UUID
    role: UserRole
    created_at: datetime
    avatar_url: str | None = None
    model_config = {"from_attributes": True}


class UsersRespond(BaseModel):
    data: list[UserRespond]
    count: int
