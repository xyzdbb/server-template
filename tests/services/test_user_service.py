import pytest
from sqlmodel import Session

from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_superuser, create_user
from app.utils.exceptions import ConflictException

def test_create_user(session: Session):
    user_in = UserCreate(email="test@example.com", password="Test1234")
    user = create_user(session, user_in)
    assert user.email == "test@example.com"
    assert user.is_active is True

def test_create_duplicate_user(session: Session):
    user_in = UserCreate(email="test@example.com", password="Test1234")
    create_user(session, user_in)
    with pytest.raises(ConflictException, match="already registered"):
        create_user(session, user_in)


def test_create_superuser(session: Session):
    user_in = UserCreate(email="admin@example.com", password="Test1234")
    user = create_superuser(session, user_in)
    assert user.email == "admin@example.com"
    assert user.is_superuser is True