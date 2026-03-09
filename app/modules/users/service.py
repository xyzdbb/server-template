from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.core.security import get_password_hash, validate_password_strength
from app.modules.users.models import User
from app.modules.users.repository import user_repository
from app.modules.users.schemas import UserCreate, UserListParams, UserUpdate
from app.utils.exceptions import ConflictException, ValidationException


def _commit_and_refresh(session: Session, user: User) -> User:
    try:
        session.commit()
        session.refresh(user)
        return user
    except SQLAlchemyError:
        session.rollback()
        raise


def create_user(session: Session, user_in: UserCreate) -> User:
    existing = user_repository.get_by_email(session, user_in.email)
    if existing:
        raise ConflictException("Email already registered")

    is_valid, error_msg = validate_password_strength(user_in.password)
    if not is_valid:
        raise ValidationException(error_msg)

    user_data = user_in.model_dump()
    user_data["hashed_password"] = get_password_hash(user_data.pop("password"))

    user = user_repository.create(session, user_data)
    return _commit_and_refresh(session, user)


def update_user(session: Session, user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        is_valid, error_msg = validate_password_strength(update_data["password"])
        if not is_valid:
            raise ValidationException(error_msg)
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    updated_user = user_repository.update(session, user, update_data)
    return _commit_and_refresh(session, updated_user)


def list_users(session: Session, params: UserListParams) -> list[User]:
    return user_repository.get_multi(
        session,
        skip=params.skip,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        search=params.search,
        is_active=params.is_active,
        is_superuser=params.is_superuser,
    )


def count_users(session: Session, params: UserListParams) -> int:
    return user_repository.count_filtered(
        session,
        search=params.search,
        is_active=params.is_active,
        is_superuser=params.is_superuser,
    )
