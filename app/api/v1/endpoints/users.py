from fastapi import APIRouter

from app.api.docs import (
    BAD_REQUEST_RESPONSE,
    FORBIDDEN_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    UNPROCESSABLE_ENTITY_RESPONSE,
)
from app.api.deps import CurrentSuperuser, CurrentUser, SessionDep, UserListDep
from app.modules.users.schemas import UserResponse, UserUpdate
from app.modules.users.service import count_users, list_users, update_user
from app.schemas.common import Page

router = APIRouter()

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Return the authenticated user's profile.",
    responses={
        400: BAD_REQUEST_RESPONSE,
        401: UNAUTHORIZED_RESPONSE,
    },
)
def read_user_me(current_user: CurrentUser):
    return current_user

@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update the authenticated user's editable profile fields.",
    responses={
        400: BAD_REQUEST_RESPONSE,
        401: UNAUTHORIZED_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def update_user_me(session: SessionDep, current_user: CurrentUser, user_in: UserUpdate):
    return update_user(session, current_user, user_in)

@router.get(
    "/",
    response_model=Page[UserResponse],
    summary="List users",
    description="Return a paginated user list for administrators with sorting, search, and status filters.",
    responses={
        401: UNAUTHORIZED_RESPONSE,
        403: FORBIDDEN_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def read_users(
    session: SessionDep,
    params: UserListDep,
    current_user: CurrentSuperuser,
):
    users = list_users(session, params)
    total = count_users(session, params)
    return Page[UserResponse](
        items=users,
        total=total,
        skip=params.skip,
        limit=params.limit,
    )