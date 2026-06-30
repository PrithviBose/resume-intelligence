import json
import logging
import os
from pathlib import Path


class MetadataFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        metadata = getattr(record, "metadata", None)
        if metadata:
            message = f"{message} | {json.dumps(metadata, default=str)}"
        return message


def setup_logging(
    *,
    level: str = "INFO",
    log_file: str | None = None,
    log_to_console: bool = True,
) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level.upper())

    formatter = MetadataFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = True


def configure_logging_from_settings(settings) -> None:
    setup_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        log_to_console=settings.log_to_console,
    )
