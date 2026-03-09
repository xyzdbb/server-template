from typing import Generic, TypeVar, Type, List, Any
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError
from app.models.base import BaseModel
from app.core.logging import logger

ModelType = TypeVar("ModelType", bound=BaseModel)

class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get(self, session: Session, id: int) -> ModelType | None:
        try:
            statement = select(self.model).where(
                self.model.id == id,
                self.model.deleted_at.is_(None)
            )
            return session.exec(statement).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__}: {e}")
            raise
    
    def get_multi(self, session: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        try:
            statement = select(self.model).where(
                self.model.deleted_at.is_(None)
            ).offset(skip).limit(limit)
            return list(session.exec(statement).all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            raise
    
    def create(self, session: Session, obj_in: dict[str, Any]) -> ModelType:
        try:
            db_obj = self.model(**obj_in)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            logger.info(f"Created {self.model.__name__} with id {db_obj.id}")
            return db_obj
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    def update(self, session: Session, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        try:
            for field, value in obj_in.items():
                setattr(db_obj, field, value)
            db_obj.updated_at = datetime.utcnow()
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise
    
    def soft_delete(self, session: Session, id: int) -> ModelType | None:
        try:
            obj = self.get(session, id)
            if obj:
                obj.deleted_at = datetime.utcnow()
                session.add(obj)
                session.commit()
            return obj
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error soft deleting {self.model.__name__}: {e}")
            raise