from sqlmodel import Session
from app.crud import user_crud

def test_create_user(session: Session):
    user_data = {"email": "test@example.com", "hashed_password": "hashed", "full_name": "Test"}
    user = user_crud.create(session, user_data)
    assert user.email == "test@example.com"
    assert user.id is not None

def test_get_by_email(session: Session):
    user_data = {"email": "test@example.com", "hashed_password": "hashed"}
    user_crud.create(session, user_data)
    user = user_crud.get_by_email(session, "test@example.com")
    assert user is not None
    assert user.email == "test@example.com"