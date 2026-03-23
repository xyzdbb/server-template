from fastapi import APIRouter

from app.api.deps import CurrentSuperuser, CurrentUser, SessionDep
from app.api.docs import (
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    UNPROCESSABLE_ENTITY_RESPONSE,
)
from app.modules.items.deps import ItemListDep
from app.modules.items.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.modules.items.service import (
    create_item,
    delete_item,
    get_item,
    list_items_with_count,
    update_item,
)
from app.schemas.common import Page

router = APIRouter()


@router.post(
    "/",
    response_model=ItemResponse,
    status_code=201,
    summary="Create item",
    description="Create a new item owned by the current user.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def create_new_item(session: SessionDep, current_user: CurrentUser, item_in: ItemCreate):
    return create_item(session, item_in, owner_id=current_user.id)


@router.get(
    "/my",
    response_model=Page[ItemResponse],
    summary="List my items",
    description="Return a paginated list of items owned by the current user.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def read_my_items(session: SessionDep, current_user: CurrentUser, params: ItemListDep):
    items, total = list_items_with_count(session, params, owner_id=current_user.id)
    return Page[ItemResponse](items=items, total=total, skip=params.skip, limit=params.limit)


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Get item",
    description="Return a single item by ID. Users can only access their own items; superusers can access any.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        404: NOT_FOUND_RESPONSE,
    },
)
def read_item(session: SessionDep, current_user: CurrentUser, item_id: int):
    return get_item(session, item_id, current_user.id, is_superuser=current_user.is_superuser)


@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Update item",
    description="Update an item's fields. Users can only update their own items; superusers can update any.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        404: NOT_FOUND_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def update_existing_item(
    session: SessionDep, current_user: CurrentUser, item_id: int, item_in: ItemUpdate
):
    return update_item(
        session, item_id, item_in, current_user.id, is_superuser=current_user.is_superuser
    )


@router.delete(
    "/{item_id}",
    status_code=204,
    summary="Delete item",
    description="Soft-delete an item. Users can only delete their own items; superusers can delete any.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        404: NOT_FOUND_RESPONSE,
    },
)
def delete_existing_item(session: SessionDep, current_user: CurrentUser, item_id: int):
    delete_item(session, item_id, current_user.id, is_superuser=current_user.is_superuser)


@router.get(
    "/",
    response_model=Page[ItemResponse],
    summary="List all items",
    description="Return a paginated list of all items. Superuser only.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def read_items(session: SessionDep, _current_user: CurrentSuperuser, params: ItemListDep):
    items, total = list_items_with_count(session, params)
    return Page[ItemResponse](items=items, total=total, skip=params.skip, limit=params.limit)
