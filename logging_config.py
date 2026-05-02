"""Central logging setup for CLI and app modules."""

import logging
import os
from pathlib import Path


_CONFIGURED = False


def configure_logging(level=None):
    """Configure root logging with console and file handlers."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    env_level = os.getenv("APP_LOG_LEVEL", "INFO").upper()
    resolved_level = (level or env_level).upper()

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "app.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, resolved_level, logging.INFO))

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name):
    """Return a module logger."""
    return logging.getLogger(name)
