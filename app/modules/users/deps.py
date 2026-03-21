from typing import Annotated

from fastapi import Depends, Query

from app.modules.users.schemas import UserListParams, UserSortField
from app.schemas.common import SortOrder


def get_user_list_params(
    skip: int = Query(default=0, ge=0, description="Number of records to skip."),
    limit: int = Query(default=100, ge=1, le=100, description="Maximum number of records to return."),
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
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        is_active=is_active,
        is_superuser=is_superuser,
    )


UserListDep = Annotated[UserListParams, Depends(get_user_list_params)]
