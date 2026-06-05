"""
Network Discovery Tool - Main Entry Point
Enterprise-grade Cisco network discovery application.
"""

import sys
import os
import logging
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from gui.main_window import MainWindow
from config import AppConfig


def setup_logging() -> None:
    """Configure root logger before GUI starts."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    from logging.handlers import RotatingFileHandler

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler(
        log_dir / "network_discovery.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
    )

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def main() -> None:
    """Application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Network Discovery Tool Starting")
    logger.info(f"Version: {AppConfig.APP_VERSION}")
    logger.info("=" * 60)

    # Ensure required directories exist
    for directory in [AppConfig.LOG_DIR, AppConfig.REPORTS_DIR, AppConfig.INPUT_DIR]:
        Path(directory).mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName(AppConfig.APP_NAME)
    app.setApplicationVersion(AppConfig.APP_VERSION)
    app.setOrganizationName("NetworkOps")

    # High-DPI support is always enabled in Qt 6 — no attribute needed.

    window = MainWindow()
    window.show()

    logger.info("GUI launched successfully")
    exit_code = app.exec()
    logger.info(f"Application exited with code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
