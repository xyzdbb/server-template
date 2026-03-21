from sqlalchemy import text
from sqlalchemy.pool import NullPool, QueuePool
from sqlmodel import Session, create_engine
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

_engine = None


def _build_engine_kwargs() -> dict:
    kwargs: dict = {"echo": not settings.IS_PRODUCTION}
    if settings.ENVIRONMENT == "test":
        kwargs["poolclass"] = NullPool
    else:
        kwargs.update(
            {
                "poolclass": QueuePool,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
            }
        )
    return kwargs


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.DATABASE_URL, **_build_engine_kwargs())
    return _engine


def reset_engine():
    """Dispose the cached engine and clear the reference.

    Call this in test teardown or when settings change to force re-creation.
    """
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def get_session():
    with Session(get_engine()) as session:
        yield session


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def check_database_health() -> bool:
    if settings.ENVIRONMENT == "test":
        return True

    try:
        with Session(get_engine()) as session:
            session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        raise Exception(f"Database health check failed: {e}") from e
