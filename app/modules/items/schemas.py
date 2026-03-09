from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import PaginationParams, SortOrder


class ItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=255, examples=["Demo item"])
    description: str | None = Field(
        default=None,
        max_length=1000,
        examples=["Short description for the item."],
    )


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    title: str | None = None


class ItemResponse(ItemBase):
    id: int = Field(examples=[1])
    owner_id: int = Field(examples=[1])

    class Config:
        from_attributes = True


class ItemListParams(PaginationParams):
    sort_by: Literal["created_at", "updated_at", "title"] = "created_at"
    sort_order: SortOrder = "desc"
    search: str | None = Field(default=None, max_length=255)
