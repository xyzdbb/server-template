from sqlmodel import Session, create_engine
from sqlalchemy.pool import QueuePool, NullPool
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.core.logging import logger

engine = create_engine(
    settings.DATABASE_URL,
    echo=not settings.IS_PRODUCTION,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    poolclass=NullPool if settings.ENVIRONMENT == "test" else QueuePool,
)

def get_session():
    try:
        with Session(engine) as session:
            yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def check_database_health() -> bool:
    try:
        with Session(engine) as session:
            session.execute("SELECT 1")
            return True
    except Exception as e:
        raise Exception(f"Database health check failed: {e}")