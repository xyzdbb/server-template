from datetime import UTC, datetime
from typing import Any, Generic, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.logging import logger
from app.models.base import TableBase
from app.schemas.common import SortOrder
from app.utils.exceptions import ValidationException

ModelType = TypeVar("ModelType", bound=TableBase)


class RepositoryBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def _apply_sort(self, statement, sort_by: str, sort_order: SortOrder):
        if not hasattr(self.model, sort_by):
            raise ValidationException(f"Invalid sort field: '{sort_by}'")
        column = getattr(self.model, sort_by)
        return statement.order_by(column.asc() if sort_order == "asc" else column.desc())

    def _count_statement(self, session: Session, statement) -> int:
        subquery = statement.subquery()
        count_statement = select(func.count()).select_from(subquery)
        return int(session.exec(count_statement).one())

    def get(self, session: Session, id: int) -> ModelType | None:
        try:
            statement = select(self.model).where(
                self.model.id == id,
                self.model.deleted_at.is_(None),
            )
            return session.exec(statement).first()
        except SQLAlchemyError as exc:
            logger.error(f"Error getting {self.model.__name__}: {exc}")
            raise

    def get_multi(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: SortOrder = "desc",
    ) -> list[ModelType]:
        try:
            statement = self._apply_sort(
                (
                select(self.model)
                .where(self.model.deleted_at.is_(None))
                .offset(skip)
                .limit(limit)
                ),
                sort_by=sort_by,
                sort_order=sort_order,
            )
            return list(session.exec(statement).all())
        except SQLAlchemyError as exc:
            logger.error(f"Error getting multiple {self.model.__name__}: {exc}")
            raise

    def count(self, session: Session) -> int:
        try:
            statement = select(self.model).where(
                self.model.deleted_at.is_(None)
            )
            return self._count_statement(session, statement)
        except SQLAlchemyError as exc:
            logger.error(f"Error counting {self.model.__name__}: {exc}")
            raise

    def create(self, session: Session, obj_in: dict[str, Any]) -> ModelType:
        try:
            db_obj = self.model(**obj_in)
            session.add(db_obj)
            session.flush()
            return db_obj
        except SQLAlchemyError as exc:
            logger.error(f"Error creating {self.model.__name__}: {exc}")
            raise

    def update(
        self,
        session: Session,
        db_obj: ModelType,
        obj_in: dict[str, Any],
    ) -> ModelType:
        try:
            for field, value in obj_in.items():
                setattr(db_obj, field, value)
            session.add(db_obj)
            session.flush()
            return db_obj
        except SQLAlchemyError as exc:
            logger.error(f"Error updating {self.model.__name__}: {exc}")
            raise

    def soft_delete(self, session: Session, id: int) -> ModelType | None:
        try:
            obj = self.get(session, id)
            if obj:
                obj.deleted_at = datetime.now(UTC)
                session.add(obj)
                session.flush()
            return obj
        except SQLAlchemyError as exc:
            logger.error(f"Error soft deleting {self.model.__name__}: {exc}")
            raise
