from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, SessionDep
from app.api.docs import (
    CONFLICT_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    UNPROCESSABLE_ENTITY_RESPONSE,
)
from app.core.limiter import limiter
from app.modules.auth.schemas import RefreshTokenRequest, Token
from app.modules.auth.service import (
    authenticate_user,
    create_user_token,
    logout_user,
    refresh_user_token,
)
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserResponse
from app.modules.users.service import create_user
from app.utils.exceptions import AuthException

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    summary="Login",
    description="Authenticate a user with username and password form data, then issue access and refresh tokens.",
    responses={
        200: {
            "description": "Authentication succeeded.",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access-token",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh-token",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: UNAUTHORIZED_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
@limiter.limit("5/minute")
def login(request: Request, session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise AuthException("Incorrect username or password")
    assert user.id is not None
    tokens = create_user_token(user.id)
    return Token(**tokens)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh tokens",
    description="Exchange a valid refresh token for a new access token pair.",
    responses={
        200: {
            "description": "Tokens refreshed successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new-access-token",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new-refresh-token",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: UNAUTHORIZED_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
@limiter.limit("20/minute")
def refresh_access_token(request: Request, session: SessionDep, body: RefreshTokenRequest) -> Token:
    tokens = refresh_user_token(session, body.refresh_token)
    return Token(**tokens)


@router.post(
    "/logout",
    status_code=204,
    summary="Logout",
    description="Revoke the provided refresh token so it can no longer be used.",
    responses={
        204: {"description": "Logout succeeded."},
        401: UNAUTHORIZED_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
def logout(body: RefreshTokenRequest, current_user: CurrentUser) -> None:
    assert current_user.id is not None
    logout_user(body.refresh_token, current_user.id)


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=201,
    summary="Create user account",
    description="Register a new user account and return the created user profile.",
    responses={
        201: {
            "description": "User created successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "johndoe",
                        "full_name": "Jane Doe",
                        "is_active": True,
                        "is_superuser": False,
                    }
                }
            },
        },
        409: CONFLICT_RESPONSE,
        422: UNPROCESSABLE_ENTITY_RESPONSE,
    },
)
@limiter.limit("3/minute")
def signup(request: Request, session: SessionDep, user_in: UserCreate) -> User:
    return create_user(session, user_in)
