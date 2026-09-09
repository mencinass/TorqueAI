import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure structured console logging for the application."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger("automotive_ai")
    logger.setLevel(log_level)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger bound to the project namespace."""
    logger = logging.getLogger("automotive_ai")
    if name:
        return logging.getLogger(f"automotive_ai.{name}")
    return logger


logger = setup_logging()

