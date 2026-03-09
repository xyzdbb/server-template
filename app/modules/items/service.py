from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.modules.items.models import Item
from app.modules.items.repository import item_repository
from app.modules.items.schemas import ItemCreate, ItemListParams, ItemUpdate
from app.modules.users.models import User
from app.utils.exceptions import NotFoundException, PermissionDeniedException


def _commit_and_refresh(session: Session, item: Item) -> Item:
    try:
        session.commit()
        session.refresh(item)
        return item
    except SQLAlchemyError:
        session.rollback()
        raise


def create_item(session: Session, item_in: ItemCreate, owner: User) -> Item:
    item_data = item_in.model_dump()
    item_data["owner_id"] = owner.id
    item = item_repository.create(session, item_data)
    return _commit_and_refresh(session, item)


def get_user_items(
    session: Session,
    owner_id: int,
    params: ItemListParams,
) -> list[Item]:
    return item_repository.get_by_owner(
        session,
        owner_id,
        skip=params.skip,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        search=params.search,
    )


def count_user_items(session: Session, owner_id: int, params: ItemListParams) -> int:
    return item_repository.count_by_owner(session, owner_id, search=params.search)


def get_user_item(session: Session, item_id: int, current_user: User) -> Item:
    item = item_repository.get(session, item_id)
    if not item:
        raise NotFoundException("Item not found")
    if item.owner_id != current_user.id:
        raise PermissionDeniedException("Not enough privileges")
    return item


def update_user_item(
    session: Session,
    item_id: int,
    item_in: ItemUpdate,
    current_user: User,
) -> Item:
    item = get_user_item(session, item_id, current_user)
    update_data = item_in.model_dump(exclude_unset=True)
    updated_item = item_repository.update(session, item, update_data)
    return _commit_and_refresh(session, updated_item)
