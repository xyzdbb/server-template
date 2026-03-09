from sqlmodel import Session
from app.core.security import get_password_hash, validate_password_strength
from app.crud import user_crud
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User

def create_user(session: Session, user_in: UserCreate) -> User:
    existing = user_crud.get_by_email(session, user_in.email)
    if existing:
        raise ValueError("Email already registered")
    
    is_valid, error_msg = validate_password_strength(user_in.password)
    if not is_valid:
        raise ValueError(error_msg)
    
    user_data = user_in.model_dump()
    user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    
    return user_crud.create(session, user_data)

def update_user(session: Session, user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        is_valid, error_msg = validate_password_strength(update_data["password"])
        if not is_valid:
            raise ValueError(error_msg)
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    return user_crud.update(session, user, update_data)