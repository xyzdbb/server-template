from sqlmodel import Session

from app.core.security import get_password_hash, validate_password_strength
from app.core.transaction import commit_and_refresh
from app.modules.users.models import User
from app.modules.users.repository import user_repository
from app.modules.users.schemas import UserCreate, UserListParams, UserUpdate
from app.utils.exceptions import ConflictException, ValidationException


def create_user(session: Session, user_in: UserCreate) -> User:
    existing = user_repository.get_by_username(session, user_in.username)
    if existing:
        raise ConflictException("Username already registered")

    is_valid, error_msg = validate_password_strength(user_in.password)
    if not is_valid:
        raise ValidationException(error_msg)

    user_data = user_in.model_dump()
    user_data["hashed_password"] = get_password_hash(user_data.pop("password"))

    user = user_repository.create(session, user_data)
    return commit_and_refresh(session, user)


def create_superuser(session: Session, user_in: UserCreate) -> User:
    user = create_user(session, user_in)
    user.is_superuser = True
    session.add(user)
    return commit_and_refresh(session, user)


def update_user(session: Session, user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        is_valid, error_msg = validate_password_strength(update_data["password"])
        if not is_valid:
            raise ValidationException(error_msg)
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    updated_user = user_repository.update(session, user, update_data)
    return commit_and_refresh(session, updated_user)


def list_users_with_count(
    session: Session, params: UserListParams
) -> tuple[list[User], int]:
    return user_repository.get_multi_with_count(
        session,
        skip=params.skip,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        search=params.search,
        is_active=params.is_active,
        is_superuser=params.is_superuser,
    )
