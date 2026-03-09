from sqlmodel import Session, select

from app.modules.items.models import Item
from app.repositories.base import RepositoryBase
from app.schemas.common import SortOrder


class ItemRepository(RepositoryBase[Item]):
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
        statement = select(Item).where(
            Item.owner_id == owner_id,
            Item.deleted_at.is_(None),
        )
        if search:
            statement = statement.where(Item.title.ilike(f"%{search.strip()}%"))
        statement = self._apply_sort(statement, sort_by=sort_by, sort_order=sort_order)
        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all())

    def count_by_owner(self, session: Session, owner_id: int, search: str | None = None) -> int:
        statement = select(Item).where(
            Item.owner_id == owner_id,
            Item.deleted_at.is_(None),
        )
        if search:
            statement = statement.where(Item.title.ilike(f"%{search.strip()}%"))
        return self._count_statement(session, statement)


item_repository = ItemRepository(Item)
