"""
Main application window for the Network Discovery Tool.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont, QTextCursor, QCloseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton,
    QComboBox, QProgressBar, QTextEdit, QFileDialog,
    QMessageBox, QSplitter, QStatusBar, QFrame,
)

from config import AppConfig
from gui.styles import MAIN_STYLESHEET, LOG_COLORS
from gui.worker import DiscoveryWorker
from gui.dialogs import AboutDialog, ErrorDialog

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self) -> None:
        super().__init__()
        self._worker: Optional[DiscoveryWorker] = None
        self._devices: List[dict] = []
        self._setup_ui()
        self._connect_signals()
        logger.info("Main window initialized.")

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setWindowTitle(AppConfig.APP_NAME)
        self.resize(AppConfig.WINDOW_WIDTH, AppConfig.WINDOW_HEIGHT)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(MAIN_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 8)
        root.setSpacing(10)

        # Title bar
        root.addWidget(self._build_title_bar())

        # Main split: left controls / right log
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 6, 0)
        left_layout.setSpacing(10)
        left_layout.addWidget(self._build_input_group())
        left_layout.addWidget(self._build_options_group())
        left_layout.addWidget(self._build_action_group())
        left_layout.addWidget(self._build_status_group())
        left_layout.addStretch()

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 0, 0, 0)
        right_layout.addWidget(self._build_log_group())

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter)

        # Progress bar
        root.addWidget(self._build_progress_bar())

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready — load an input file to begin.")

    def _build_title_bar(self) -> QWidget:
        frame = QFrame()
        frame.setMaximumHeight(52)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 0, 4, 0)

        title = QLabel(AppConfig.APP_NAME)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #6fa3d8;")

        subtitle = QLabel(f"v{AppConfig.APP_VERSION}  |  Enterprise Network Automation")
        subtitle.setStyleSheet("color: #6b7a8d; font-size: 12px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()

        about_btn = QPushButton("About")
        about_btn.setFixedWidth(70)
        about_btn.clicked.connect(lambda: AboutDialog(self).exec())
        layout.addWidget(about_btn)
        return frame

    def _build_input_group(self) -> QGroupBox:
        grp = QGroupBox("Input / Output")
        layout = QVBoxLayout(grp)
        layout.setSpacing(8)

        # Input file
        row1 = QHBoxLayout()
        lbl1 = QLabel("Input Excel:")
        lbl1.setFixedWidth(90)
        self._txt_input = QLineEdit()
        self._txt_input.setPlaceholderText("Select input.xlsx …")
        self._txt_input.setReadOnly(True)
        btn_browse_input = QPushButton("Browse")
        btn_browse_input.setFixedWidth(80)
        btn_browse_input.clicked.connect(self._browse_input)
        row1.addWidget(lbl1)
        row1.addWidget(self._txt_input)
        row1.addWidget(btn_browse_input)
        layout.addLayout(row1)

        # Output folder
        row2 = QHBoxLayout()
        lbl2 = QLabel("Output Folder:")
        lbl2.setFixedWidth(90)
        self._txt_output = QLineEdit()
        self._txt_output.setPlaceholderText("Select output directory …")
        self._txt_output.setReadOnly(True)
        self._txt_output.setText(str(AppConfig.REPORTS_DIR.resolve()))
        btn_browse_output = QPushButton("Browse")
        btn_browse_output.setFixedWidth(80)
        btn_browse_output.clicked.connect(self._browse_output)
        row2.addWidget(lbl2)
        row2.addWidget(self._txt_output)
        row2.addWidget(btn_browse_output)
        layout.addLayout(row2)

        return grp

    def _build_options_group(self) -> QGroupBox:
        grp = QGroupBox("Options")
        layout = QHBoxLayout(grp)

        lbl = QLabel("Threads:")
        self._combo_threads = QComboBox()
        for t in AppConfig.THREAD_OPTIONS:
            self._combo_threads.addItem(str(t), t)
        self._combo_threads.setCurrentText(str(AppConfig.DEFAULT_THREADS))
        self._combo_threads.setFixedWidth(90)

        layout.addWidget(lbl)
        layout.addWidget(self._combo_threads)
        layout.addStretch()
        return grp

    def _build_action_group(self) -> QGroupBox:
        grp = QGroupBox("Actions")
        layout = QHBoxLayout(grp)
        layout.setSpacing(10)

        self._btn_start = QPushButton("▶  Start Discovery")
        self._btn_start.setObjectName("btn_start")
        self._btn_start.setEnabled(False)

        self._btn_stop = QPushButton("■  Stop")
        self._btn_stop.setObjectName("btn_stop")
        self._btn_stop.setEnabled(False)

        self._btn_export_logs = QPushButton("Export Logs")
        self._btn_export_logs.setObjectName("btn_export")

        self._btn_clear_log = QPushButton("Clear Log")

        layout.addWidget(self._btn_start)
        layout.addWidget(self._btn_stop)
        layout.addStretch()
        layout.addWidget(self._btn_export_logs)
        layout.addWidget(self._btn_clear_log)
        return grp

    def _build_status_group(self) -> QGroupBox:
        grp = QGroupBox("Status Summary")
        layout = QHBoxLayout(grp)
        layout.setSpacing(0)

        def _card(obj_name: str, caption: str) -> QWidget:
            card = QWidget()
            vl = QVBoxLayout(card)
            vl.setSpacing(2)
            vl.setContentsMargins(14, 8, 14, 8)
            num = QLabel("0")
            num.setObjectName(obj_name)
            num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cap = QLabel(caption)
            cap.setObjectName("lbl_caption")
            cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl.addWidget(num)
            vl.addWidget(cap)
            return card, num

        sep_style = "background: #3d4756; max-width: 1px;"

        card_total, self._lbl_total = _card("lbl_status_total", "TOTAL")
        layout.addWidget(card_total)

        sep1 = QFrame(); sep1.setStyleSheet(sep_style); layout.addWidget(sep1)

        card_done, self._lbl_completed = _card("lbl_status_completed", "COMPLETED")
        layout.addWidget(card_done)

        sep2 = QFrame(); sep2.setStyleSheet(sep_style); layout.addWidget(sep2)

        card_fail, self._lbl_failed = _card("lbl_status_failed", "FAILED")
        layout.addWidget(card_fail)

        sep3 = QFrame(); sep3.setStyleSheet(sep_style); layout.addWidget(sep3)

        card_run, self._lbl_running = _card("lbl_status_running", "RUNNING")
        layout.addWidget(card_run)

        return grp

    def _build_log_group(self) -> QGroupBox:
        grp = QGroupBox("Real-Time Log")
        layout = QVBoxLayout(grp)

        self._log_window = QTextEdit()
        self._log_window.setReadOnly(True)
        self._log_window.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._log_window)
        return grp

    def _build_progress_bar(self) -> QProgressBar:
        self._progress = QProgressBar()
        self._progress.setValue(0)
        self._progress.setFormat("Idle")
        self._progress.setFixedHeight(22)
        return self._progress

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._btn_start.clicked.connect(self._start_discovery)
        self._btn_stop.clicked.connect(self._stop_discovery)
        self._btn_export_logs.clicked.connect(self._export_logs)
        self._btn_clear_log.clicked.connect(self._log_window.clear)
        self._txt_input.textChanged.connect(self._update_start_button)

    # ------------------------------------------------------------------
    # File / directory browsers
    # ------------------------------------------------------------------

    def _browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Input Excel File",
            str(AppConfig.INPUT_DIR),
            "Excel Files (*.xlsx *.xls)",
        )
        if path:
            self._txt_input.setText(path)
            self._load_devices(path)

    def _browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self._txt_output.text()
        )
        if path:
            self._txt_output.setText(path)

    # ------------------------------------------------------------------
    # Device loading
    # ------------------------------------------------------------------

    def _load_devices(self, path: str) -> None:
        """Parse input Excel and populate self._devices."""
        try:
            df = pd.read_excel(path, sheet_name=AppConfig.INPUT_SHEET_NAME, dtype=str)
            df.columns = [c.strip() for c in df.columns]

            missing = [c for c in AppConfig.REQUIRED_COLUMNS if c not in df.columns]
            if missing:
                self._show_error(
                    "Invalid Input File",
                    f"Missing required columns: {', '.join(missing)}\n\n"
                    f"Expected: {', '.join(AppConfig.REQUIRED_COLUMNS)}",
                )
                self._devices = []
                return

            df = df.dropna(subset=["IP"])
            df = df.fillna("")
            self._devices = df[AppConfig.REQUIRED_COLUMNS].to_dict("records")

            self._log(f"Loaded {len(self._devices)} device(s) from {Path(path).name}.", "SUCCESS")
            self._lbl_total.setText(str(len(self._devices)))
            self._status_bar.showMessage(
                f"{len(self._devices)} device(s) loaded — ready to start."
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to load input file: %s", exc)
            self._show_error("File Load Error", f"Could not read input file:\n{exc}")
            self._devices = []

    def _update_start_button(self) -> None:
        self._btn_start.setEnabled(
            bool(self._txt_input.text()) and not (self._worker and self._worker.isRunning())
        )

    # ------------------------------------------------------------------
    # Discovery control
    # ------------------------------------------------------------------

    def _start_discovery(self) -> None:
        if not self._devices:
            self._show_error("No Devices", "No devices loaded. Please select an input file.")
            return

        output_dir = self._txt_output.text().strip()
        if not output_dir:
            self._show_error("No Output Folder", "Please select an output folder.")
            return

        thread_count = self._combo_threads.currentData()

        self._reset_counters()
        self._progress.setValue(0)
        self._progress.setFormat("Starting…")

        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)

        self._worker = DiscoveryWorker(self._devices, output_dir, thread_count, parent=self)
        self._worker.sig_log.connect(self._log)
        self._worker.sig_progress.connect(self._update_progress)
        self._worker.sig_counters.connect(self._update_counters)
        self._worker.sig_finished.connect(self._on_finished)
        self._worker.sig_error.connect(self._on_error)
        self._worker.start()

        self._status_bar.showMessage(
            f"Discovery running — {len(self._devices)} devices, {thread_count} threads."
        )
        self._log(
            f"Discovery started: {len(self._devices)} devices, {thread_count} thread(s).", "INFO"
        )

    def _stop_discovery(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._btn_stop.setEnabled(False)

    # ------------------------------------------------------------------
    # Worker signal handlers
    # ------------------------------------------------------------------

    def _update_progress(self, done: int, total: int) -> None:
        if total == 0:
            return
        pct = int(done / total * 100)
        self._progress.setValue(pct)
        self._progress.setFormat(f"{done}/{total}  ({pct}%)")

    def _update_counters(self, total: int, completed: int, failed: int, running: int) -> None:
        self._lbl_total.setText(str(total))
        self._lbl_completed.setText(str(completed))
        self._lbl_failed.setText(str(failed))
        self._lbl_running.setText(str(running))

    def _on_finished(self, output_path: str) -> None:
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._progress.setFormat("Complete")
        self._status_bar.showMessage(f"Done — report saved to: {output_path}")

        reply = QMessageBox.question(
            self,
            "Discovery Complete",
            f"Network discovery finished.\n\nReport saved to:\n{output_path}\n\nOpen report folder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            import subprocess, sys
            folder = str(Path(output_path).parent)
            if sys.platform == "win32":
                subprocess.Popen(["explorer", folder])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])

    def _on_error(self, message: str) -> None:
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._progress.setFormat("Error")
        self._show_error("Discovery Error", message)

    # ------------------------------------------------------------------
    # Log window
    # ------------------------------------------------------------------

    def _log(self, message: str, level: str = "INFO") -> None:
        """Append a coloured line to the log window (thread-safe via Qt signals)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = LOG_COLORS.get(level.upper(), LOG_COLORS["INFO"])
        html = (
            f'<span style="color:#6b7a8d;">[{timestamp}]</span> '
            f'<span style="color:{color};">{message}</span>'
        )
        self._log_window.append(html)
        # Auto-scroll
        cursor = self._log_window.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._log_window.setTextCursor(cursor)

    # ------------------------------------------------------------------
    # Export logs
    # ------------------------------------------------------------------

    def _export_logs(self) -> None:
        log_src = AppConfig.LOG_DIR / "network_discovery.log"
        if not log_src.exists():
            self._show_error("No Logs", "No log file found.")
            return

        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Export Log File",
            f"network_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            "Log Files (*.log *.txt)",
        )
        if dest:
            shutil.copy2(log_src, dest)
            self._log(f"Logs exported to: {dest}", "SUCCESS")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reset_counters(self) -> None:
        for lbl in (self._lbl_total, self._lbl_completed, self._lbl_failed, self._lbl_running):
            lbl.setText("0")
        self._lbl_total.setText(str(len(self._devices)))

    def _show_error(self, title: str, message: str) -> None:
        ErrorDialog(title, message, parent=self).exec()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._worker and self._worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Discovery Running",
                "Discovery is still running. Stop and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._worker.stop()
                self._worker.wait(5000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
