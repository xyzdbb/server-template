from datetime import timedelta
from sqlmodel import Session
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.config import settings
from app.crud import user_crud
from app.models.user import User

def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = user_crud.get_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_user_token(user_id: int) -> dict[str, str]:
    access_token = create_access_token(subject=user_id)
    refresh_token = create_refresh_token(subject=user_id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }