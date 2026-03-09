import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.logging import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"request_id={getattr(request.state, 'request_id', 'N/A')} "
            f"method={request.method} path={request.url.path} "
            f"status={response.status_code} duration={process_time:.3f}s"
        )
        return response