import logging
import sys

from pythonjsonlogger import jsonlogger

from app.core.context import request_id_ctx


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get("")
        return True


def setup_logging() -> logging.Logger:
    app_logger = logging.getLogger("app")
    if app_logger.handlers:
        return app_logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(request_id)s %(message)s",
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    app_logger.addHandler(handler)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    return app_logger


logger = setup_logging()
