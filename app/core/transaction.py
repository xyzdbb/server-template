from typing import TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

ModelType = TypeVar("ModelType")


def commit_and_refresh(session: Session, instance: ModelType) -> ModelType:
    try:
        session.commit()
        session.refresh(instance)
        return instance
    except SQLAlchemyError:
        session.rollback()
        raise
