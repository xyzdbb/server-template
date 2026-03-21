import os
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-bytes!!")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "app")
os.environ.setdefault("REDIS_URL", "memory://")
os.environ.setdefault("FIRST_SUPERUSER", "admin@example.com")
os.environ.setdefault("FIRST_SUPERUSER_PASSWORD", "Admin1234")

from app.core.limiter import limiter
from app.main import app
from app.api.deps import get_session


class FakeRedis:
    """测试用内存 Redis 替身，实现业务代码所需的 set/get/exists/delete 接口"""

    def __init__(self):
        self._store: dict[str, str] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self._store[key] = value
        return True

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def exists(self, *keys: str) -> int:
        return sum(1 for k in keys if k in self._store)

    def delete(self, *keys: str) -> int:
        count = sum(1 for k in keys if k in self._store)
        for k in keys:
            self._store.pop(k, None)
        return count


@pytest.fixture(autouse=True)
def _mock_redis():
    fake = FakeRedis()
    with patch("app.modules.auth.service.get_redis", return_value=fake):
        yield


@pytest.fixture(autouse=True)
def _disable_rate_limit():
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
