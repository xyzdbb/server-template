import logging
import sys

from pythonjsonlogger import jsonlogger


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        from app.middleware.request_id import request_id_ctx
        record.request_id = request_id_ctx.get("")
        return True


def setup_logging():
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(request_id)s %(message)s",
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    root.addHandler(handler)
    root.setLevel(logging.INFO)
    return root


logger = setup_logging()
