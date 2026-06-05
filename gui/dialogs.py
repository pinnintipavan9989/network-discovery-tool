"""
Reusable PyQt6 dialog windows.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class AboutDialog(QDialog):
    """Simple about box."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Network Discovery Tool")
        self.setFixedSize(420, 280)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Network Discovery Tool")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel("Version 1.0.0  |  Enterprise Edition")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        sep = QLabel("─" * 50)
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sep)

        info_text = (
            "Automated Cisco network discovery platform.\n\n"
            "Collects CDP, VLAN, SVI, EtherChannel, and\n"
            "gateway data from 500+ devices concurrently.\n\n"
            "Built with Python 3.12 · Netmiko · PyQt6 · Genie"
        )
        info = QLabel(info_text)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        btn = QPushButton("Close")
        btn.clicked.connect(self.accept)
        btn.setFixedWidth(100)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn)
        h.addStretch()
        layout.addLayout(h)


class ErrorDialog(QDialog):
    """Display a detailed error message."""

    def __init__(self, title: str, message: str, detail: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        if detail:
            txt = QTextEdit()
            txt.setReadOnly(True)
            txt.setPlainText(detail)
            txt.setMaximumHeight(150)
            layout.addWidget(txt)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)
