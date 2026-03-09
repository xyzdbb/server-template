from sqlmodel import Session, select

from app.modules.items.models import Item
from app.repositories.base import RepositoryBase
from app.schemas.common import SortOrder


class ItemRepository(RepositoryBase[Item]):
    def _build_owner_statement(self, owner_id: int, search: str | None = None):
        statement = select(Item).where(
            Item.owner_id == owner_id,
            Item.deleted_at.is_(None),
        )
        if search:
            statement = statement.where(Item.title.ilike(f"%{search.strip()}%"))
        return statement

    def get_by_owner(
        self,
        session: Session,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: SortOrder = "desc",
        search: str | None = None,
    ) -> list[Item]:
        statement = self._build_owner_statement(owner_id, search)
        statement = self._apply_sort(statement, sort_by=sort_by, sort_order=sort_order)
        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all())

    def get_by_owner_with_count(
        self,
        session: Session,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: SortOrder = "desc",
        search: str | None = None,
    ) -> tuple[list[Item], int]:
        base = self._build_owner_statement(owner_id, search)
        total = self._count_statement(session, base)
        statement = self._apply_sort(base, sort_by=sort_by, sort_order=sort_order)
        statement = statement.offset(skip).limit(limit)
        items = list(session.exec(statement).all())
        return items, total


item_repository = ItemRepository(Item)
