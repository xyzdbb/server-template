from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.modules.auth.service import get_current_active_user
from app.modules.items.schemas import ItemListParams
from app.modules.users.models import User
from app.modules.users.schemas import UserListParams
from app.schemas.common import SortOrder
from app.utils.exceptions import PermissionDeniedException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

SessionDep = Annotated[Session, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_user_list_params(
    skip: int = Query(default=0, ge=0, description="Number of records to skip."),
    limit: int = Query(default=100, ge=1, le=100, description="Maximum number of records to return."),
    sort_by: str = Query(
        default="created_at",
        pattern="^(created_at|updated_at|email)$",
        description="Field used to sort the user list.",
    ),
    sort_order: SortOrder = Query(default="desc", description="Sort direction."),
    search: str | None = Query(
        default=None,
        max_length=255,
        description="Case-insensitive match against user email and full name.",
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


def get_item_list_params(
    skip: int = Query(default=0, ge=0, description="Number of records to skip."),
    limit: int = Query(default=100, ge=1, le=100, description="Maximum number of records to return."),
    sort_by: str = Query(
        default="created_at",
        pattern="^(created_at|updated_at|title)$",
        description="Field used to sort the item list.",
    ),
    sort_order: SortOrder = Query(default="desc", description="Sort direction."),
    search: str | None = Query(
        default=None,
        max_length=255,
        description="Case-insensitive match against item title.",
    ),
) -> ItemListParams:
    return ItemListParams(
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
    )


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    return get_current_active_user(session, token)


CurrentUser = Annotated[User, Depends(get_current_user)]
UserListDep = Annotated[UserListParams, Depends(get_user_list_params)]
ItemListDep = Annotated[ItemListParams, Depends(get_item_list_params)]


def get_current_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise PermissionDeniedException("Not enough privileges")
    return current_user


CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
