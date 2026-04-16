# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
MedPharm ERP - Login Dialog
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LoginDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.authenticated_user = None
        self.setWindowTitle("MedPharm ERP - Login")
        self.setFixedSize(420, 480)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #00BCD4; border-radius: 0;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(40, 30, 40, 30)

        title = QLabel("MedPharm ERP")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)

        subtitle = QLabel("Medical & Pharmaceutical Management")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 13px; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        # Form
        form_container = QFrame()
        form_container.setStyleSheet("background-color: #1a1d23;")
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(40, 30, 40, 30)
        form_layout.setSpacing(16)

        form_layout.addWidget(QLabel("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(40)
        form_layout.addWidget(self.username_input)

        form_layout.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        form_layout.addWidget(self.password_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #E53935; font-size: 12px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        form_layout.addWidget(self.error_label)

        form_layout.addSpacing(8)

        login_btn = QPushButton("Sign In")
        login_btn.setObjectName("primary_button")
        login_btn.setMinimumHeight(44)
        login_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        login_btn.clicked.connect(self.attempt_login)
        form_layout.addWidget(login_btn)

        self.password_input.returnPressed.connect(self.attempt_login)
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())

        form_layout.addStretch()

        hint = QLabel("Demo: dr.carter / doctor123")
        hint.setStyleSheet("color: #505050; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(hint)

        copyright_label = QLabel("\u00a9 2026 Enlightec Ltd.")
        copyright_label.setStyleSheet("color: #505050; font-size: 10px;")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(copyright_label)

        layout.addWidget(form_container)

    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.show_error("Please enter both username and password")
            return

        user = self.db_manager.authenticate_user(username, password)
        if user:
            self.authenticated_user = user
            self.accept()
        else:
            self.show_error("Invalid username or password")
            self.password_input.clear()
            self.password_input.setFocus()

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()
