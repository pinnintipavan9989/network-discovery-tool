"""
Application-wide configuration constants and defaults.
"""

from pathlib import Path


class AppConfig:
    """Central configuration for the Network Discovery Tool."""

    APP_NAME = "Network Discovery Tool"
    APP_VERSION = "1.0.0"

    # Directories
    BASE_DIR = Path(__file__).parent
    LOG_DIR = BASE_DIR / "logs"
    REPORTS_DIR = BASE_DIR / "reports"
    INPUT_DIR = BASE_DIR / "input"

    # SSH defaults
    SSH_TIMEOUT = 30          # seconds
    SSH_AUTH_TIMEOUT = 20     # seconds
    SSH_BANNER_TIMEOUT = 15   # seconds
    COMMAND_TIMEOUT = 60      # seconds
    MAX_RETRIES = 2

    # Threading
    DEFAULT_THREADS = 10
    THREAD_OPTIONS = [5, 10, 20, 50, 100]

    # Excel
    INPUT_SHEET_NAME = "Devices"
    REQUIRED_COLUMNS = ["IP", "Username", "Password", "Device_Type"]

    OUTPUT_SHEET_DISCOVERY = "Network Discovery"
    OUTPUT_SHEET_ETHERCHANNEL = "Ethernet Channels"
    OUTPUT_SHEET_FAILED = "Failed Devices"

    # Colors (ARGB hex for openpyxl)
    COLOR_HEADER_BG = "1F4E79"      # Dark blue
    COLOR_HEADER_FG = "FFFFFF"      # White
    COLOR_SUCCESS_BG = "C6EFCE"     # Light green
    COLOR_FAILED_BG = "FFC7CE"      # Light red
    COLOR_ALT_ROW = "DEEAF1"        # Light blue alternate
    COLOR_TABLE_BORDER = "9DC3E6"   # Border blue

    # Logging
    LOG_MAX_BYTES = 10 * 1024 * 1024   # 10 MB
    LOG_BACKUP_COUNT = 5

    # GUI
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
