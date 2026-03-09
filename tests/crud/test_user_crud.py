from sqlmodel import Session

from app.modules.users.repository import user_repository

def test_create_user(session: Session):
    user_data = {"email": "test@example.com", "hashed_password": "hashed", "full_name": "Test"}
    user = user_repository.create(session, user_data)
    assert user.email == "test@example.com"
    assert user.id is not None

def test_get_by_email(session: Session):
    user_data = {"email": "test@example.com", "hashed_password": "hashed"}
    user_repository.create(session, user_data)
    user = user_repository.get_by_email(session, "test@example.com")
    assert user is not None
    assert user.email == "test@example.com"