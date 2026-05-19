from __future__ import annotations

import logging
import os
import sys
from typing import Final

from dotenv import load_dotenv

load_dotenv()

TRUE_VALUES: Final[set[str]] = {"1", "true", "yes", "on"}


def get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in TRUE_VALUES


def get_log_level(default: str = "INFO") -> int:
    level_name = os.getenv("LOG_LEVEL", default).strip().upper()
    return getattr(logging, level_name, logging.INFO)


def setup_logging() -> None:
    level = get_log_level()
    debug_enabled = get_bool_env("DEBUG", False)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Reduce noisy framework logs unless debug is explicitly enabled.
    noisy_loggers = {
        "uvicorn": logging.INFO if debug_enabled else logging.WARNING,
        "uvicorn.error": logging.INFO if debug_enabled else logging.WARNING,
        "uvicorn.access": logging.INFO if debug_enabled else logging.WARNING,
        "sqlalchemy.engine": logging.INFO if debug_enabled else logging.WARNING,
        "sqlalchemy.pool": logging.INFO if debug_enabled else logging.WARNING,
    }

    for logger_name, logger_level in noisy_loggers.items():
        logging.getLogger(logger_name).setLevel(logger_level)

    if not debug_enabled:
        # Hide access logs completely when not debugging.
        logging.getLogger("uvicorn.access").propagate = False

