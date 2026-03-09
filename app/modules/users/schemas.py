from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import PaginationParams, SortOrder


class UserBase(BaseModel):
    email: EmailStr = Field(examples=["user@example.com"])
    full_name: str | None = Field(default=None, examples=["Jane Doe"])


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40, examples=["StrongPass123"])


class UserUpdate(UserBase):
    email: EmailStr | None = None
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=40,
        examples=["NewStrongPass123"],
    )


class UserResponse(UserBase):
    id: int = Field(examples=[1])
    is_active: bool = Field(examples=[True])
    is_superuser: bool = Field(examples=[False])

    class Config:
        from_attributes = True


class UserListParams(PaginationParams):
    sort_by: Literal["created_at", "updated_at", "email"] = "created_at"
    sort_order: SortOrder = "desc"
    search: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
