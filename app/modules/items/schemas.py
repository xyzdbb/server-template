from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginationParams, SortOrder


class ItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=255, examples=["My Item"])
    description: str | None = Field(default=None, max_length=1000, examples=["A useful item"])


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255, examples=["Updated Item"])
    description: str | None = Field(default=None, max_length=1000, examples=["Updated description"])


class ItemResponse(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    owner_id: int = Field(examples=[1])


ItemSortField = Literal["created_at", "updated_at", "title"]


class ItemListParams(PaginationParams):
    sort_by: ItemSortField = "created_at"
    sort_order: SortOrder = "desc"
    search: str | None = Field(default=None, max_length=255)
