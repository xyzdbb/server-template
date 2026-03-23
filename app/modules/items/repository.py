from typing import Any

from sqlalchemy import Select
from sqlmodel import Session, select

from app.modules.items.models import Item
from app.repositories.base import RepositoryBase
from app.schemas.common import SortOrder


class ItemRepository(RepositoryBase[Item]):
    def _build_filtered_statement(
        self,
        owner_id: int | None = None,
        search: str | None = None,
    ) -> Select[Any]:
        statement = select(Item).where(Item.deleted_at.is_(None))
        if owner_id is not None:
            statement = statement.where(Item.owner_id == owner_id)
        if search:
            statement = statement.where(Item.title.ilike(f"%{search.strip()}%"))
        return statement

    def get_multi_with_count(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: SortOrder = "desc",
        owner_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Item], int]:
        base = self._build_filtered_statement(owner_id=owner_id, search=search)
        total = self._count_statement(session, base)
        statement = self._apply_sort(base, sort_by=sort_by, sort_order=sort_order)
        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all()), total


item_repository = ItemRepository(Item)
