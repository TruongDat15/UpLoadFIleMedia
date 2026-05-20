import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


def setup_logging() -> None:
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    console = logging.StreamHandler()
    console.setFormatter(fmt)

    # File — xoay mỗi ngày, giữ 7 ngày
    file_handler = TimedRotatingFileHandler(
        filename=f"{LOG_DIR}/app.log",
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)

    logging.basicConfig(level=logging.INFO, handlers=[console, file_handler])