from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func
from sqlmodel import Session, select

from app.models.base import TableBase
from app.schemas.common import SortOrder
from app.utils.exceptions import ValidationException

ModelType = TypeVar("ModelType", bound=TableBase)


class RepositoryBase(Generic[ModelType]):
    """通用 CRUD 仓储基类，提供软删除、分页排序等标准操作。"""

    _protected_fields: frozenset[str] = frozenset({"id", "created_at", "updated_at", "deleted_at"})

    @staticmethod
    def _escape_like(term: str) -> str:
        """转义 LIKE 通配符，防止用户输入的 % 和 _ 被当作模式匹配。"""
        return term.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    def _apply_sort(
        self, statement: Select[Any], sort_by: str, sort_order: SortOrder
    ) -> Select[Any]:
        if not hasattr(self.model, sort_by):
            raise ValidationException(f"Invalid sort field: '{sort_by}'")
        column = getattr(self.model, sort_by)
        return statement.order_by(column.asc() if sort_order == "asc" else column.desc())

    def _count_statement(self, session: Session, statement: Select[Any]) -> int:
        subquery = statement.subquery()
        count_statement = select(func.count()).select_from(subquery)
        return int(session.exec(count_statement).one())

    def get(self, session: Session, id: int) -> ModelType | None:
        statement = select(self.model).where(
            self.model.id == id,
            self.model.deleted_at.is_(None),
        )
        return session.exec(statement).first()

    def get_multi(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: SortOrder = "desc",
    ) -> list[ModelType]:
        statement = select(self.model).where(self.model.deleted_at.is_(None))
        statement = self._apply_sort(statement, sort_by=sort_by, sort_order=sort_order)
        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all())

    def count(self, session: Session) -> int:
        statement = select(self.model).where(
            self.model.deleted_at.is_(None)
        )
        return self._count_statement(session, statement)

    def create(self, session: Session, obj_in: dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        session.flush()
        return db_obj

    def update(
        self,
        session: Session,
        db_obj: ModelType,
        obj_in: dict[str, Any],
    ) -> ModelType:
        for field, value in obj_in.items():
            if field not in self._protected_fields:
                setattr(db_obj, field, value)
        session.add(db_obj)
        session.flush()
        return db_obj

    def soft_delete(self, session: Session, target: int | ModelType) -> ModelType | None:
        """标记记录为已删除（设置 deleted_at），不执行物理删除。

        ``target`` 可以是主键 ID 或已加载的模型实例。
        """
        obj = self.get(session, target) if isinstance(target, int) else target
        if obj:
            obj.deleted_at = datetime.now(UTC)
            session.add(obj)
            session.flush()
        return obj
