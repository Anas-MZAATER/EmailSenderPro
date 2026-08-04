"""Centralized logging configuration."""
import logging
import sys
from pathlib import Path


def setup_logging() -> None:
    """Configure file + console logging."""
    log_path = Path("app.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
