from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from llm_sqa.config import ensure_project_directories, get_settings


def configure_logging() -> None:
    ensure_project_directories()
    settings = get_settings()
    log_file = settings.log_dir / "app.log"

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    root_logger.addHandler(console)
    root_logger.addHandler(file_handler)
