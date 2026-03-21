import time

from app.core.context import request_id_ctx
from app.core.logging import logger


class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            method = scope.get("method", "")
            path = scope.get("path", "")
            rid = request_id_ctx.get("")
            logger.info(
                "request completed",
                extra={
                    "request_id": rid,
                    "method": method,
                    "path": path,
                    "status": status_code,
                    "duration": f"{duration:.3f}s",
                },
            )
