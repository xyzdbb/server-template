from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class TableBase(SQLModel):
    # sqlmodel Field 与 pydantic mypy 插件重载不完全对齐
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(  # type: ignore[call-overload]
        default_factory=utc_now, sa_type=DateTime(timezone=True)
    )
    updated_at: datetime = Field(  # type: ignore[call-overload]
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": utc_now},
    )
    deleted_at: datetime | None = Field(  # type: ignore[call-overload]
        default=None, sa_type=DateTime(timezone=True)
    )