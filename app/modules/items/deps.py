from typing import Annotated

from fastapi import Depends, Query

from app.modules.items.schemas import ItemListParams, ItemSortField
from app.schemas.common import PaginationParams, SortOrder


def get_item_list_params(
    pagination: PaginationParams = Depends(),
    sort_by: ItemSortField = Query(default="created_at", description="Field used to sort the item list."),
    sort_order: SortOrder = Query(default="desc", description="Sort direction."),
    search: str | None = Query(
        default=None,
        max_length=255,
        description="Case-insensitive match against item title.",
    ),
) -> ItemListParams:
    return ItemListParams(
        skip=pagination.skip,
        limit=pagination.limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
    )


ItemListDep = Annotated[ItemListParams, Depends(get_item_list_params)]
