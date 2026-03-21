import redis

from app.core.config import settings
from app.core.logging import logger

_pool: redis.ConnectionPool | None = None


def _get_pool() -> redis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL, decode_responses=True
        )
    return _pool


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=_get_pool())


def close_redis() -> None:
    global _pool
    if _pool is not None:
        _pool.disconnect()
        _pool = None
        logger.info("Redis connection pool closed")
