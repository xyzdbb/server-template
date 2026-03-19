import pytest
from sqlmodel import Session

from app.modules.users.schemas import UserCreate, UserUpdate
from app.modules.users.service import create_superuser, create_user, update_user
from app.utils.exceptions import ConflictException, ValidationException


def test_create_user(session: Session):
    user_in = UserCreate(username="testuser", password="Test1234")
    user = create_user(session, user_in)
    assert user.username == "testuser"
    assert user.is_active is True


def test_create_duplicate_user(session: Session):
    user_in = UserCreate(username="testuser", password="Test1234")
    create_user(session, user_in)
    with pytest.raises(ConflictException, match="already registered"):
        create_user(session, user_in)


def test_create_superuser(session: Session):
    user_in = UserCreate(username="adminuser", password="Test1234")
    user = create_superuser(session, user_in)
    assert user.username == "adminuser"
    assert user.is_superuser is True


def test_update_user_full_name(session: Session):
    user = create_user(session, UserCreate(username="upduser", password="Test1234"))
    updated = update_user(session, user, UserUpdate(full_name="New Name"))
    assert updated.full_name == "New Name"


def test_update_user_password(session: Session):
    from app.core.security import verify_password

    user = create_user(session, UserCreate(username="pwduser", password="Test1234"))
    updated = update_user(session, user, UserUpdate(password="NewPass5678"))
    assert verify_password("NewPass5678", updated.hashed_password)


def test_update_user_weak_password_raises(session: Session):
    user = create_user(session, UserCreate(username="weakuser", password="Test1234"))
    with pytest.raises(ValidationException):
        update_user(session, user, UserUpdate(password="weakpass1"))
