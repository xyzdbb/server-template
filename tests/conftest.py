import os
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient
from testcontainers.postgres import PostgresContainer

# Docker Desktop (macOS/Windows) 的 socket 不在默认路径，自动探测
if "DOCKER_HOST" not in os.environ:
    _desktop_sock = Path.home() / ".docker" / "run" / "docker.sock"
    if _desktop_sock.exists():
        os.environ["DOCKER_HOST"] = f"unix://{_desktop_sock}"

# 禁用 Ryuk（testcontainers 清理容器），用 context manager 自行管理生命周期
os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")

# settings 初始化所需的环境变量，测试数据库实际由 testcontainers 管理
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-bytes!!")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "app")
os.environ.setdefault("REDIS_URL", "memory://")
os.environ.setdefault("FIRST_SUPERUSER", "admin@example.com")
os.environ.setdefault("FIRST_SUPERUSER_PASSWORD", "Admin1234")

from app.core.database import reset_engine
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


@pytest.fixture(scope="session")
def _pg_container():
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as pg:
        yield pg


@pytest.fixture(scope="session")
def _engine(_pg_container):
    engine = create_engine(_pg_container.get_connection_url())
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


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


@pytest.fixture(autouse=True)
def _reset_db_engine():
    yield
    reset_engine()


@pytest.fixture(name="session")
def session_fixture(_engine):
    conn = _engine.connect()
    txn = conn.begin()
    session = Session(bind=conn)
    yield session
    session.close()
    txn.rollback()
    conn.close()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
