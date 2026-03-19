from sqlmodel import Session

from app.core.config import settings
from app.core.redis import get_redis
from app.core.security import (
    DUMMY_HASH,
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.modules.users.models import User
from app.modules.users.repository import user_repository
from app.utils.exceptions import AuthException, ValidationException

REFRESH_TOKEN_KEY_PREFIX = "refresh_token:"
REFRESH_TOKEN_TTL_SECONDS = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60


async def _store_refresh_jti(jti: str, user_id: int) -> None:
    r = get_redis()
    await r.set(
        f"{REFRESH_TOKEN_KEY_PREFIX}{jti}",
        str(user_id),
        ex=REFRESH_TOKEN_TTL_SECONDS,
    )


async def _verify_refresh_jti(jti: str) -> bool:
    r = get_redis()
    return await r.exists(f"{REFRESH_TOKEN_KEY_PREFIX}{jti}") > 0


async def _revoke_refresh_jti(jti: str) -> None:
    r = get_redis()
    await r.delete(f"{REFRESH_TOKEN_KEY_PREFIX}{jti}")


def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = user_repository.get_by_username(session, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user_token(user_id: int) -> dict[str, str]:
    access_token = create_access_token(subject=user_id)
    refresh_token, jti = create_refresh_token(subject=user_id)
    await _store_refresh_jti(jti, user_id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


async def refresh_user_token(session: Session, refresh_token: str) -> dict[str, str]:
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = int(payload.get("sub"))
        old_jti = payload.get("jti")
    except (InvalidTokenError, TypeError, ValueError) as exc:
        raise AuthException("Invalid refresh token") from exc

    if old_jti and not await _verify_refresh_jti(old_jti):
        raise AuthException("Refresh token has been revoked")

    user = user_repository.get(session, user_id)
    if not user or not user.is_active:
        raise AuthException("Invalid refresh token")

    if old_jti:
        await _revoke_refresh_jti(old_jti)

    return await create_user_token(user.id)


async def logout_user(refresh_token: str) -> None:
    """撤销 refresh token，使其不可再用于刷新"""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        jti = payload.get("jti")
    except (InvalidTokenError, TypeError, ValueError) as exc:
        raise AuthException("Invalid refresh token") from exc

    if jti:
        await _revoke_refresh_jti(jti)


def get_current_active_user(session: Session, token: str) -> User:
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload.get("sub"))
    except (InvalidTokenError, TypeError, ValueError) as exc:
        raise AuthException("Could not validate credentials") from exc

    user = user_repository.get(session, user_id)
    if not user:
        raise AuthException("Could not validate credentials")
    if not user.is_active:
        raise ValidationException("Inactive user")
    return user
