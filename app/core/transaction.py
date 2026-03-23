from typing import TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, Session

T = TypeVar("T", bound=SQLModel)


def safe_commit(session: Session) -> None:
    """Commit with rollback on failure. Use for operations that don't need refresh (e.g. delete)."""
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise


def commit_and_refresh(session: Session, instance: T, *extra: T) -> T:
    """Commit and refresh all given instances. Returns the first one for convenience."""
    try:
        session.commit()
        session.refresh(instance)
        for obj in extra:
            session.refresh(obj)
        return instance
    except SQLAlchemyError:
        session.rollback()
        raise
