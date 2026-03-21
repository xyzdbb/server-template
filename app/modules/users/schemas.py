from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginationParams


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=255, examples=["johndoe"])
    full_name: str | None = Field(default=None, max_length=255, examples=["Jane Doe"])


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40, examples=["StrongPass123"])


class UserUpdate(BaseModel):
    """所有字段均为可选，仅更新显式传入的字段。"""
    full_name: str | None = Field(default=None, max_length=255, examples=["Jane Doe"])
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=40,
        examples=["NewStrongPass123"],
    )


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    is_active: bool = Field(examples=[True])
    is_superuser: bool = Field(examples=[False])


UserSortField = Literal["created_at", "updated_at", "username"]


class UserListParams(PaginationParams):
    sort_by: UserSortField = "created_at"
    search: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
