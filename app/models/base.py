from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class TableBase(SQLModel):
    # 插入前可为 None；从库加载后的实例在业务路径上必有 id。需要 int 时请用 pk，避免到处断言。
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": utc_now},
    )
    deleted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

    @property
    def pk(self) -> int:
        """已落库实体的主键；未 flush 前访问会抛错。"""
        if self.id is None:
            raise RuntimeError("Primary key is not set; entity may not be persisted yet")
        return self.id