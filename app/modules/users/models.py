from sqlalchemy import Index, text
from sqlmodel import Field

from app.models.base import TableBase


class User(TableBase, table=True):
    __table_args__ = (
        Index(
            "ix_user_not_deleted",
            "id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    username: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
