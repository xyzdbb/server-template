import os

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient

# 让测试独立于本地/CI 的环境变量与 .env 文件
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-bytes!!")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "app")
os.environ.setdefault("FIRST_SUPERUSER", "admin@example.com")
os.environ.setdefault("FIRST_SUPERUSER_PASSWORD", "Admin1234")

from app.main import app
from app.api.deps import get_session


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
