import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.context import request_id_ctx
from app.core.logging import logger

_Scope = dict[str, Any]
_Message = dict[str, Any]
_Receive = Callable[[], Awaitable[_Message]]
_Send = Callable[[_Message], Awaitable[None]]
_ASGIApp = Callable[[_Scope, _Receive, _Send], Awaitable[None]]


class LoggingMiddleware:
    def __init__(self, app: _ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        status_code = 500

        async def send_wrapper(message: _Message) -> None:
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
