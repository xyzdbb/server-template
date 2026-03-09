from sqlmodel import Session, select
from app.crud.base import CRUDBase
from app.models.item import Item

class CRUDItem(CRUDBase[Item]):
    def get_by_owner(self, session: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[Item]:
        statement = select(Item).where(
            Item.owner_id == owner_id,
            Item.deleted_at.is_(None)
        ).offset(skip).limit(limit)
        return list(session.exec(statement).all())

item_crud = CRUDItem(Item)