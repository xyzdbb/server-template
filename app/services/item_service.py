from sqlmodel import Session
from app.crud import item_crud
from app.schemas.item import ItemCreate
from app.models.item import Item
from app.models.user import User

def create_item(session: Session, item_in: ItemCreate, owner: User) -> Item:
    item_data = item_in.model_dump()
    item_data["owner_id"] = owner.id
    return item_crud.create(session, item_data)

def get_user_items(session: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[Item]:
    return item_crud.get_by_owner(session, owner_id, skip, limit)