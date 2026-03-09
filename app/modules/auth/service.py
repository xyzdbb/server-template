from sqlmodel import Session

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


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = user_repository.get_by_email(session, email)
    if not user:
        # 执行 dummy 验证以抹平用户不存在与密码错误的响应时间差，防止时序攻击枚举邮箱
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user_token(user_id: int) -> dict[str, str]:
    access_token = create_access_token(subject=user_id)
    refresh_token = create_refresh_token(subject=user_id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def refresh_user_token(session: Session, refresh_token: str) -> dict[str, str]:
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = int(payload.get("sub"))
    except (InvalidTokenError, TypeError, ValueError) as exc:
        raise AuthException("Invalid refresh token") from exc

    user = user_repository.get(session, user_id)
    if not user or not user.is_active:
        raise AuthException("Invalid refresh token")

    return create_user_token(user.id)


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
