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
from app.utils.exceptions import AuthException

REFRESH_TOKEN_KEY_PREFIX = "refresh_token:"
REFRESH_TOKEN_TTL_SECONDS = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60


def _extract_user_id(payload: dict) -> int:
    sub = payload.get("sub")
    if sub is None:
        raise AuthException("Token missing subject claim")
    return int(sub)


def _store_refresh_jti(jti: str, user_id: int) -> None:
    r = get_redis()
    r.set(
        f"{REFRESH_TOKEN_KEY_PREFIX}{jti}",
        str(user_id),
        ex=REFRESH_TOKEN_TTL_SECONDS,
    )


def _verify_refresh_jti(jti: str) -> bool:
    r = get_redis()
    return r.exists(f"{REFRESH_TOKEN_KEY_PREFIX}{jti}") > 0


def _revoke_refresh_jti(jti: str) -> None:
    r = get_redis()
    r.delete(f"{REFRESH_TOKEN_KEY_PREFIX}{jti}")


def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = user_repository.get_by_username(session, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user_token(user_id: int) -> dict[str, str]:
    access_token = create_access_token(subject=user_id)
    refresh_token, jti = create_refresh_token(subject=user_id)
    _store_refresh_jti(jti, user_id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def refresh_user_token(session: Session, refresh_token: str) -> dict[str, str]:
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = _extract_user_id(payload)
        old_jti = payload.get("jti")
    except (InvalidTokenError, ValueError) as exc:
        raise AuthException("Invalid refresh token") from exc

    if old_jti and not _verify_refresh_jti(old_jti):
        raise AuthException("Refresh token has been revoked")

    user = user_repository.get(session, user_id)
    if not user or not user.is_active:
        if old_jti:
            _revoke_refresh_jti(old_jti)
        raise AuthException("Invalid refresh token")

    if old_jti:
        _revoke_refresh_jti(old_jti)

    return create_user_token(user.id)


def logout_user(refresh_token: str, current_user_id: int) -> None:
    """撤销 refresh token，使其不可再用于刷新；校验 token 归属当前用户"""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        token_user_id = _extract_user_id(payload)
        jti = payload.get("jti")
    except (InvalidTokenError, ValueError) as exc:
        raise AuthException("Invalid refresh token") from exc

    if token_user_id != current_user_id:
        raise AuthException("Refresh token does not belong to the current user")

    if jti:
        _revoke_refresh_jti(jti)


def get_current_active_user(session: Session, token: str) -> User:
    try:
        payload = decode_token(token, expected_type="access")
        user_id = _extract_user_id(payload)
    except (InvalidTokenError, ValueError) as exc:
        raise AuthException("Could not validate credentials") from exc

    user = user_repository.get(session, user_id)
    if not user:
        raise AuthException("Could not validate credentials")
    if not user.is_active:
        raise AuthException("Inactive user")
    return user
