from fastapi import APIRouter, Path

from app.api.docs import (
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    UNPROCESSABLE_ENTITY_RESPONSE,
)
from app.api.deps import CurrentUser, ItemListDep, SessionDep
from app.modules.items.schemas import ItemCreate, ItemUpdate, ItemResponse
from app.modules.items.service import (
    count_user_items,
    create_item,
    get_user_item,
    get_user_items,
    update_user_item,
)
from app.schemas.common import Page

router = APIRouter()

@router.post(
    "/",
    response_model=ItemResponse,
    status_code=201,
    summary="Create item",
    description="Create a new item owned by the authenticated user.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def create_new_item(session: SessionDep, current_user: CurrentUser, item_in: ItemCreate):
    item = create_item(session, item_in, current_user)
    return item

@router.get(
    "/",
    response_model=Page[ItemResponse],
    summary="List items",
    description="Return the authenticated user's items with pagination, sorting, and title search.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    params: ItemListDep,
):
    items = get_user_items(session, current_user.id, params)
    total = count_user_items(session, current_user.id, params)
    return Page[ItemResponse](
        items=items,
        total=total,
        skip=params.skip,
        limit=params.limit,
    )

@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Get item",
    description="Return a single item owned by the authenticated user.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        404: NOT_FOUND_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def read_item(
    session: SessionDep,
    current_user: CurrentUser,
    item_id: int = Path(description="Unique identifier of the item."),
):
    return get_user_item(session, item_id, current_user)

@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Update item",
    description="Update an item owned by the authenticated user.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        404: NOT_FOUND_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def update_item(
    session: SessionDep,
    current_user: CurrentUser,
    item_id: int = Path(description="Unique identifier of the item."),
    item_in: ItemUpdate = ...,
):
    return update_user_item(session, item_id, item_in, current_user)