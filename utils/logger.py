"""
utils/logger.py
---------------------------------------
Centralized logging.
MoodFlix AI

Usage:
    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("...")
    log.exception("...")   # inside an except block, logs full traceback
"""

import logging
import os
import sys


def configure_logging(app=None):
    """Call once at startup (from app.py)."""

    level = logging.DEBUG if os.getenv("FLASK_ENV") == "development" else logging.INFO

    root = logging.getLogger("moodflix")
    root.setLevel(level)

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
        ))
        root.addHandler(handler)

    # Quiet down noisy third-party loggers unless we're debugging.
    if level != logging.DEBUG:
        logging.getLogger("pymongo").setLevel(logging.WARNING)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)

    return root


def get_logger(name):
    return logging.getLogger(f"moodflix.{name}")
