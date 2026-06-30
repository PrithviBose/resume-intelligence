import logging
from typing import Any


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    **metadata: Any,
) -> None:
    logger.log(level, event, extra={"metadata": metadata})
