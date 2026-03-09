from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")
SortOrder = Literal["asc", "desc"]


class Message(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str = Field(
        examples=["Incorrect email or password"],
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


class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=100)