"""Simple logger helper for AppsAnalyst.

Provides a small `setup_logger` convenience to configure a named logger with
stream output and a readable formatter. The function is idempotent (it won't
add duplicate handlers if called multiple times).
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


def setup_logger(name: str = "AppsAnalyst", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger for the application.

    Parameters
    - name: logger name (default: "AppsAnalyst")
    - level: logging level (default: logging.INFO)

    Returns
    - configured logging.Logger instance
    """
    logger = logging.getLogger(name)

    # If already configured, return as-is to avoid duplicate handlers
    if any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.setLevel(level)
        return logger

    logger.setLevel(level)

    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
