from sqlmodel import Session, select

from app.modules.users.models import User
from app.repositories.base import RepositoryBase
from app.schemas.common import SortOrder


class UserRepository(RepositoryBase[User]):
    def _build_filtered_statement(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
    ):
        statement = select(User).where(User.deleted_at.is_(None))
        if search:
            search_term = f"%{search.strip()}%"
            statement = statement.where(
                User.email.ilike(search_term) | User.full_name.ilike(search_term)
            )
        if is_active is not None:
            statement = statement.where(User.is_active.is_(is_active))
        if is_superuser is not None:
            statement = statement.where(User.is_superuser.is_(is_superuser))
        return statement

    def get_multi(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: SortOrder = "desc",
        search: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
    ) -> list[User]:
        statement = self._build_filtered_statement(
            search=search, is_active=is_active, is_superuser=is_superuser
        )
        statement = self._apply_sort(statement, sort_by=sort_by, sort_order=sort_order)
        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all())

    def get_multi_with_count(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: SortOrder = "desc",
        search: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
    ) -> tuple[list[User], int]:
        base = self._build_filtered_statement(
            search=search, is_active=is_active, is_superuser=is_superuser
        )
        total = self._count_statement(session, base)
        statement = self._apply_sort(base, sort_by=sort_by, sort_order=sort_order)
        statement = statement.offset(skip).limit(limit)
        items = list(session.exec(statement).all())
        return items, total

    def get_by_email(self, session: Session, email: str) -> User | None:
        statement = select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
        return session.exec(statement).first()

    def get_active_users(self, session: Session) -> list[User]:
        statement = select(User).where(
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
        return list(session.exec(statement).all())


user_repository = UserRepository(User)
