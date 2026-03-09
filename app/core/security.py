from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 用于时序攻击防护：当用户不存在时执行此 dummy 哈希以抹平响应时间差
DUMMY_HASH = pwd_context.hash("dummy-password-for-timing-safety")


class InvalidTokenError(Exception):
    pass


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str | Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if len(password) > 40:
        return False, "Password must be less than 40 characters"
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
