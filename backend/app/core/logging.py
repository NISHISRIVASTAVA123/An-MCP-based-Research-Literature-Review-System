"""Structured Logging Module.

Provides standard academic and operational logging format across providers and services.
"""

import logging
import sys
from backend.app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures root application logger."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("academic_lit_review")
    logger.setLevel(log_level)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = setup_logging()

