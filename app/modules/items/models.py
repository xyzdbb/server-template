from sqlmodel import Field

from app.models.base import TableBase


class Item(TableBase, table=True):
    title: str = Field(index=True, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    owner_id: int = Field(foreign_key="user.id")
