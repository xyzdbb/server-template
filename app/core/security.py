from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import bcrypt
import jwt

from app.core.config import settings

# 用于时序攻击防护：当用户不存在时执行此 dummy 校验以抹平响应时间差
DUMMY_HASH: str = bcrypt.hashpw(
    b"dummy-password-for-timing-safety",
    bcrypt.gensalt(),
).decode("utf-8")


class InvalidTokenError(Exception):
    pass


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str | Any) -> tuple[str, str]:
    """返回 (token, jti)，调用方需将 jti 存入 Redis"""
    jti = uuid4().hex
    expire = datetime.now(UTC) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh", "jti": jti}
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # 例如 bcrypt 会拒绝超过 72 bytes 的 password
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def validate_password_strength(password: str) -> tuple[bool, str]:
    """校验密码字符类别（长度由 Pydantic schema 约束，此处不重复检查）"""
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase"
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain digit"
    return True, ""


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if expected_type and token_type != expected_type:
            raise InvalidTokenError(f"Invalid token type: expected {expected_type}")
        return payload
    except jwt.PyJWTError as e:
        raise InvalidTokenError(f"Invalid token: {e}") from e
