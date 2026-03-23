import math
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field, computed_field

T = TypeVar("T")
SortOrder = Literal["asc", "desc"]


class Message(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str = Field(
        examples=["Incorrect username or password"],
        description="Human-readable error description.",
    )


class HealthStatus(BaseModel):
    status: str = Field(examples=["ok"])
    database: str = Field(examples=["up"])


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    skip: int = Field(ge=0)
    limit: int = Field(gt=0)

    @computed_field
    @property
    def current_page(self) -> int:
        return self.skip // self.limit + 1

    @computed_field
    @property
    def total_pages(self) -> int:
        return math.ceil(self.total / self.limit) if self.total > 0 else 0

    @computed_field
    @property
    def has_next(self) -> bool:
        return (self.skip + self.limit) < self.total

    @computed_field
    @property
    def has_previous(self) -> bool:
        return self.skip > 0


class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: SortOrder = "desc"