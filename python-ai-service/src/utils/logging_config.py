import logging
import sys
from logging.handlers import RotatingFileHandler

LOG_FORMAT = "%(asctime)s [%(threadName)s] %(levelname)-5s %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO", log_file: str | None = None):
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console)

    # File handler (production)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=100 * 1024 * 1024, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root_logger.addHandler(file_handler)

    # Reduce noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger
