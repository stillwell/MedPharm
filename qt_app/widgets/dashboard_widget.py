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
MedPharm ERP - Dashboard Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class DashboardWidget(QWidget):
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()
        self.refresh_data()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(60000)

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)

        # Header
        header = QLabel(f"Welcome, {self.current_user.get('display_title', 'User')}")
        header.setObjectName("heading")
        self.main_layout.addWidget(header)

        subtitle = QLabel("Dashboard Overview")
        subtitle.setObjectName("subheading")
        self.main_layout.addWidget(subtitle)

        # KPI Cards
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(16)
        self.kpi_cards = {}
        kpi_defs = [
            ("patient_count", "Total Patients", "#00BCD4"),
            ("active_prescriptions", "Active Rx", "#43A047"),
            ("today_appointments", "Today's Appts", "#FB8C00"),
            ("monthly_revenue", "Monthly Revenue", "#7C4DFF"),
            ("pending_bills", "Pending Bills", "#E53935"),
            ("controlled_substances", "Controlled Rx", "#FF5722"),
        ]
        for key, label, color in kpi_defs:
            card = self._create_kpi_card(label, "0", color)
            self.kpi_cards[key] = card
            self.kpi_layout.addWidget(card["frame"])

        self.main_layout.addLayout(self.kpi_layout)

        # Bottom section: appointments + activity
        bottom = QHBoxLayout()
        bottom.setSpacing(20)

        # Today's Appointments
        appt_frame = QFrame()
        appt_frame.setObjectName("card")
        appt_layout = QVBoxLayout(appt_frame)
        appt_title = QLabel("Today's Appointments")
        appt_title.setObjectName("section_title")
        appt_layout.addWidget(appt_title)

        self.appt_table = QTableWidget()
        self.appt_table.setColumnCount(5)
        self.appt_table.setHorizontalHeaderLabels(["Time", "Patient", "Type", "Status", "Reason"])
        self.appt_table.horizontalHeader().setStretchLastSection(True)
        self.appt_table.setAlternatingRowColors(True)
        self.appt_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.appt_table.verticalHeader().setVisible(False)
        self.appt_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        appt_layout.addWidget(self.appt_table)
        bottom.addWidget(appt_frame, 3)

        # Recent Activity
        activity_frame = QFrame()
        activity_frame.setObjectName("card")
        activity_layout = QVBoxLayout(activity_frame)
        activity_title = QLabel("Recent Activity")
        activity_title.setObjectName("section_title")
        activity_layout.addWidget(activity_title)

        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(3)
        self.activity_table.setHorizontalHeaderLabels(["Action", "By", "When"])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        activity_layout.addWidget(self.activity_table)
        bottom.addWidget(activity_frame, 2)

        self.main_layout.addLayout(bottom)
        self.main_layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _create_kpi_card(self, label, value, color):
        frame = QFrame()
        frame.setObjectName("kpi_card")
        frame.setStyleSheet(f"""
            QFrame#kpi_card {{
                border-top: 3px solid {color};
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)

        val_label = QLabel(value)
        val_label.setObjectName("card_value")
        val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(val_label)

        name_label = QLabel(label)
        name_label.setObjectName("card_label")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        return {"frame": frame, "value_label": val_label, "name_label": name_label}

    def refresh_data(self):
        try:
            stats = self.db_manager.get_dashboard_stats()
            for key, card in self.kpi_cards.items():
                val = stats.get(key, 0)
                if key in ("monthly_revenue", "pending_bills", "today_revenue"):
                    card["value_label"].setText(f"${val:,.2f}")
                else:
                    card["value_label"].setText(str(val))

            # Appointments
            appts = self.db_manager.get_todays_appointments(
                provider_id=self.current_user.get("id")
            )
            self.appt_table.setRowCount(len(appts))
            for i, a in enumerate(appts):
                dt = a.get("scheduled_datetime", "")
                if dt:
                    from datetime import datetime
                    try:
                        t = datetime.fromisoformat(dt)
                        dt = t.strftime("%I:%M %p")
                    except (ValueError, TypeError):
                        pass
                self.appt_table.setItem(i, 0, QTableWidgetItem(str(dt)))
                self.appt_table.setItem(i, 1, QTableWidgetItem(a.get("patient_name", "")))
                self.appt_table.setItem(i, 2, QTableWidgetItem(a.get("appointment_type", "").replace("_", " ").title()))
                self.appt_table.setItem(i, 3, QTableWidgetItem(a.get("status", "").replace("_", " ").title()))
                self.appt_table.setItem(i, 4, QTableWidgetItem(a.get("reason", "")))

            # Activity
            activity = self.db_manager.get_recent_activity(10)
            self.activity_table.setRowCount(len(activity))
            for i, a in enumerate(activity):
                self.activity_table.setItem(i, 0, QTableWidgetItem(a.get("action", "")))
                self.activity_table.setItem(i, 1, QTableWidgetItem(a.get("user", "")))
                ts = a.get("timestamp", "")
                if ts:
                    from datetime import datetime
                    try:
                        t = datetime.fromisoformat(ts)
                        ts = t.strftime("%m/%d %I:%M %p")
                    except (ValueError, TypeError):
                        pass
                self.activity_table.setItem(i, 2, QTableWidgetItem(str(ts)))
        except Exception as e:
            print(f"Dashboard refresh error: {e}")
