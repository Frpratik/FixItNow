import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict
from app.core.config import settings

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            log_obj["event"] = record.event
        if hasattr(record, "booking_id"):
            log_obj["booking_id"] = str(record.booking_id)
        if hasattr(record, "user_id"):
            log_obj["user_id"] = str(record.user_id)
        if hasattr(record, "mechanic_id"):
            log_obj["mechanic_id"] = str(record.mechanic_id)
        if hasattr(record, "extra_data"):
            log_obj["data"] = record.extra_data
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    # Silence verbose loggers
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("fixitnow")
