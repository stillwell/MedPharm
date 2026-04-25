# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
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
MedPharm ERP - Main Window
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QStatusBar, QMenuBar, QFrame, QMessageBox,
    QApplication
)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QAction, QFont

from qt_app.styles import STYLESHEET
from qt_app.dialogs.login_dialog import LoginDialog
from qt_app.widgets.dashboard_widget import DashboardWidget
from qt_app.widgets.patient_widget import PatientWidget
from qt_app.widgets.prescription_widget import PrescriptionWidget
from qt_app.widgets.medication_widget import MedicationWidget
from qt_app.widgets.appointment_widget import AppointmentWidget
from qt_app.widgets.records_widget import RecordsWidget
from qt_app.widgets.billing_widget import BillingWidget
from qt_app.widgets.symptoms_widget import SymptomsWidget
from qt_app.widgets.analytics_widget import AnalyticsWidget
from qt_app.widgets.messages_widget import MessagesWidget


class MainWindow(QMainWindow):
    NAV_ITEMS = [
        ("Dashboard", "dashboard"),
        ("Patients", "patients"),
        ("Prescriptions", "prescriptions"),
        ("Medications", "medications"),
        ("Appointments", "appointments"),
        ("Records", "records"),
        ("Billing", "billing"),
        ("Messages", "messages"),
        ("Symptoms", "symptoms"),
        ("Analytics", "analytics"),
    ]

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = None
        self.setWindowTitle("MedPharm ERP - Medical & Pharmaceutical Management System")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(STYLESHEET)
        self.nav_buttons = []

        if not self.do_login():
            QTimer.singleShot(0, QApplication.instance().quit)
            return

        self.setup_ui()
        self.setup_menu()
        self.setup_statusbar()
        self.navigate_to(0)

    def do_login(self) -> bool:
        dialog = LoginDialog(self.db_manager, self)
        if dialog.exec() == LoginDialog.DialogCode.Accepted:
            self.current_user = dialog.authenticated_user
            return True
        return False

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo area
        logo_frame = QFrame()
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 20, 16, 20)
        logo_label = QLabel("MedPharm ERP")
        logo_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        logo_label.setStyleSheet("color: #00BCD4;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)

        role_label = QLabel(self.current_user.role.value.title() if self.current_user else "")
        role_label.setStyleSheet("color: #808080; font-size: 11px;")
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(role_label)
        sidebar_layout.addWidget(logo_frame)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #2a2d35;")
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(8)

        # Nav buttons
        for i, (label, _) in enumerate(self.NAV_ITEMS):
            btn = QPushButton(f"  {label}")
            btn.setObjectName("nav_button")
            btn.setCheckable(True)
            btn.setMinimumHeight(44)
            btn.setFont(QFont("Segoe UI", 12))
            btn.clicked.connect(lambda checked, idx=i: self.navigate_to(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # User info at bottom
        user_frame = QFrame()
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(16, 8, 16, 16)
        if self.current_user:
            user_name = QLabel(self.current_user.full_name)
            user_name.setStyleSheet("color: #e0e0e0; font-weight: 600; font-size: 12px;")
            user_layout.addWidget(user_name)
        sidebar_layout.addWidget(user_frame)

        main_layout.addWidget(sidebar)

        # Content area
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background-color: #1a1d23; }")

        user_dict = {
            "id": self.current_user.id,
            "full_name": self.current_user.full_name,
            "role": self.current_user.role.value,
            "display_title": self.current_user.display_title
        } if self.current_user else {}

        self.stack.addWidget(DashboardWidget(self.db_manager, user_dict))
        self.stack.addWidget(PatientWidget(self.db_manager, user_dict))
        self.stack.addWidget(PrescriptionWidget(self.db_manager, user_dict))
        self.stack.addWidget(MedicationWidget(self.db_manager, user_dict))
        self.stack.addWidget(AppointmentWidget(self.db_manager, user_dict))
        self.stack.addWidget(RecordsWidget(self.db_manager, user_dict))
        self.stack.addWidget(BillingWidget(self.db_manager, user_dict))
        self.stack.addWidget(MessagesWidget(self.db_manager, user_dict))
        self.stack.addWidget(SymptomsWidget(self.db_manager, user_dict))
        self.stack.addWidget(AnalyticsWidget(self.db_manager, user_dict))

        main_layout.addWidget(self.stack)

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("Tools")
        refresh_action = QAction("Refresh Data", self)
        refresh_action.triggered.connect(self.refresh_current)
        tools_menu.addAction(refresh_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_statusbar(self):
        status = QStatusBar()
        self.setStatusBar(status)

        if self.current_user:
            status.addWidget(QLabel(f"  Logged in as: {self.current_user.display_title}"))

        self.time_label = QLabel()
        status.addPermanentWidget(self.time_label)

        self.update_time()
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)

        status.addPermanentWidget(QLabel("Database: Connected  "))

    def update_time(self):
        self.time_label.setText(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss  "))

    def navigate_to(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh_data"):
            widget.refresh_data()

    def refresh_current(self):
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh_data"):
            widget.refresh_data()

    def logout(self):
        reply = QMessageBox.question(
            self, "Logout", "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()

    def show_about(self):
        QMessageBox.about(
            self, "About MedPharm ERP",
            "<h2>MedPharm ERP v1.7.5</h2>"
            "<p>Medical & Pharmaceutical Enterprise Resource Planning System</p>"
            "<p>Comprehensive ERP for medical practices with prescription management, "
            "patient records, billing, and pharmaceutical database.</p>"
            "<p>&copy; 2026 Enlightec Ltd.</p>"
        )
