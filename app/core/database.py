from sqlalchemy import text
from sqlalchemy.pool import QueuePool, NullPool
from sqlmodel import Session, create_engine
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.core.logging import logger

engine_kwargs = {
    "echo": not settings.IS_PRODUCTION,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

if settings.ENVIRONMENT == "test":
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs.update(
        {
            "poolclass": QueuePool,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
        }
    )

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

def get_session():
    try:
        with Session(engine) as session:
            yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def check_database_health() -> bool:
    if settings.ENVIRONMENT == "test":
        return True

    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        raise Exception(f"Database health check failed: {e}")