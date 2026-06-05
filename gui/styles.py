"""
PyQt6 stylesheet for the Network Discovery Tool.
Professional dark theme.
"""

MAIN_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e2329;
    color: #e8eaed;
    font-family: "Segoe UI", "SF Pro Display", Arial, sans-serif;
    font-size: 13px;
}

QGroupBox {
    background-color: #252b35;
    border: 1px solid #3d4756;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: 600;
    font-size: 12px;
    color: #9fafbf;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #252b35;
    color: #6fa3d8;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #2d333d;
    border: 1px solid #3d4756;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e8eaed;
    selection-background-color: #1f4e79;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #4d90d0;
    background-color: #333b47;
}

QLineEdit:read-only {
    color: #9fafbf;
    background-color: #252b35;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #9fafbf;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #2d333d;
    border: 1px solid #4d90d0;
    selection-background-color: #1f4e79;
    color: #e8eaed;
    outline: none;
}

QPushButton {
    background-color: #2d6db5;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 12px;
    min-height: 32px;
    min-width: 90px;
}

QPushButton:hover {
    background-color: #3a84d6;
}

QPushButton:pressed {
    background-color: #1f5899;
}

QPushButton:disabled {
    background-color: #3d4756;
    color: #6b7a8d;
}

QPushButton#btn_start {
    background-color: #1a7a42;
    min-width: 130px;
    font-size: 13px;
}

QPushButton#btn_start:hover {
    background-color: #22a356;
}

QPushButton#btn_stop {
    background-color: #8b2020;
    min-width: 130px;
    font-size: 13px;
}

QPushButton#btn_stop:hover {
    background-color: #b52828;
}

QPushButton#btn_stop:disabled {
    background-color: #3d4756;
    color: #6b7a8d;
}

QPushButton#btn_export {
    background-color: #5a4a8a;
}

QPushButton#btn_export:hover {
    background-color: #7060b0;
}

QTextEdit {
    background-color: #141a22;
    color: #c8d8e8;
    border: 1px solid #3d4756;
    border-radius: 4px;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 11px;
    padding: 4px;
    selection-background-color: #1f4e79;
}

QProgressBar {
    background-color: #2d333d;
    border: 1px solid #3d4756;
    border-radius: 5px;
    text-align: center;
    color: #e8eaed;
    font-weight: 600;
    font-size: 11px;
    min-height: 20px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a6fa8, stop:1 #22a356);
    border-radius: 4px;
}

QLabel {
    color: #c8d8e8;
    background: transparent;
}

QLabel#lbl_status_total {
    font-size: 22px;
    font-weight: 700;
    color: #6fa3d8;
}

QLabel#lbl_status_completed {
    font-size: 22px;
    font-weight: 700;
    color: #22a356;
}

QLabel#lbl_status_failed {
    font-size: 22px;
    font-weight: 700;
    color: #e05555;
}

QLabel#lbl_status_running {
    font-size: 22px;
    font-weight: 700;
    color: #e8a020;
}

QLabel#lbl_caption {
    font-size: 10px;
    color: #6b7a8d;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QScrollBar:vertical {
    background: #1e2329;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #3d4756;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #4d5f74;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QSplitter::handle {
    background-color: #3d4756;
    width: 2px;
}

QStatusBar {
    background-color: #151b23;
    color: #6b7a8d;
    border-top: 1px solid #3d4756;
    font-size: 11px;
    padding: 2px 8px;
}

QToolTip {
    background-color: #333b47;
    color: #e8eaed;
    border: 1px solid #4d90d0;
    border-radius: 4px;
    padding: 4px 8px;
}
"""

LOG_COLORS = {
    "INFO": "#c8d8e8",
    "SUCCESS": "#22a356",
    "WARNING": "#e8a020",
    "ERROR": "#e05555",
    "DEBUG": "#7a8a9a",
    "CONNECTING": "#6fa3d8",
}
