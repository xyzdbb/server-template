from typing import TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

ModelType = TypeVar("ModelType")


def commit_and_refresh(session: Session, instance: ModelType, *extra: ModelType) -> ModelType:
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
