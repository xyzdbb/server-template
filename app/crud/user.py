from sqlmodel import Session, select
from app.crud.base import CRUDBase
from app.models.user import User

class CRUDUser(CRUDBase[User]):
    def get_by_email(self, session: Session, email: str) -> User | None:
        statement = select(User).where(
            User.email == email,
            User.deleted_at.is_(None)
        )
        return session.exec(statement).first()
    
    def get_active_users(self, session: Session) -> list[User]:
        statement = select(User).where(
            User.is_active == True,
            User.deleted_at.is_(None)
        )
        return list(session.exec(statement).all())

user_crud = CRUDUser(User)