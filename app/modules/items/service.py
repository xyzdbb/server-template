from sqlmodel import Session

from app.core.transaction import commit_and_refresh
from app.modules.items.models import Item
from app.modules.items.repository import item_repository
from app.modules.items.schemas import ItemCreate, ItemListParams, ItemUpdate
from app.utils.exceptions import NotFoundException, PermissionDeniedException


def _get_item_or_404(session: Session, item_id: int) -> Item:
    item = item_repository.get(session, item_id)
    if not item:
        raise NotFoundException("Item not found")
    return item


def _check_owner(item: Item, user_id: int, *, is_superuser: bool) -> None:
    if not is_superuser and item.owner_id != user_id:
        raise PermissionDeniedException("Not the owner of this item")


def create_item(session: Session, item_in: ItemCreate, owner_id: int) -> Item:
    item_data = item_in.model_dump()
    item_data["owner_id"] = owner_id
    item = item_repository.create(session, item_data)
    return commit_and_refresh(session, item)


def get_item(session: Session, item_id: int, user_id: int, *, is_superuser: bool) -> Item:
    item = _get_item_or_404(session, item_id)
    _check_owner(item, user_id, is_superuser=is_superuser)
    return item


def update_item(
    session: Session, item_id: int, item_in: ItemUpdate, user_id: int, *, is_superuser: bool
) -> Item:
    item = _get_item_or_404(session, item_id)
    _check_owner(item, user_id, is_superuser=is_superuser)
    update_data = item_in.model_dump(exclude_unset=True)
    updated = item_repository.update(session, item, update_data)
    return commit_and_refresh(session, updated)


def delete_item(session: Session, item_id: int, user_id: int, *, is_superuser: bool) -> None:
    item = _get_item_or_404(session, item_id)
    _check_owner(item, user_id, is_superuser=is_superuser)
    item_repository.soft_delete(session, item_id)
    session.commit()


def list_items_with_count(
    session: Session, params: ItemListParams, *, owner_id: int | None = None
) -> tuple[list[Item], int]:
    return item_repository.get_multi_with_count(
        session,
        skip=params.skip,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        owner_id=owner_id,
        search=params.search,
    )
