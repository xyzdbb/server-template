from typing import Annotated

from fastapi import Depends, Query

from app.modules.users.schemas import UserListParams, UserSortField
from app.schemas.common import PaginationParams, SortOrder


def get_user_list_params(
    pagination: PaginationParams = Depends(),
    sort_by: UserSortField = Query(default="created_at", description="Field used to sort the user list."),
    sort_order: SortOrder = Query(default="desc", description="Sort direction."),
    search: str | None = Query(
        default=None,
        max_length=255,
        description="Case-insensitive match against username and full name.",
    ),
    is_active: bool | None = Query(default=None, description="Filter users by active status."),
    is_superuser: bool | None = Query(default=None, description="Filter users by superuser status."),
) -> UserListParams:
    return UserListParams(
        skip=pagination.skip,
        limit=pagination.limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        is_active=is_active,
        is_superuser=is_superuser,
    )


UserListDep = Annotated[UserListParams, Depends(get_user_list_params)]
