from sqlalchemy import Index, text
from sqlmodel import Field

from app.models.base import TableBase


class Item(TableBase, table=True):
    __table_args__ = (
        Index(
            "ix_item_not_deleted",
            "id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    title: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, max_length=1000)
    owner_id: int = Field(foreign_key="user.id", index=True)
