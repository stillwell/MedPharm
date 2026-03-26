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
MedPharm ERP - Appointment Scheduling Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QSplitter, QCalendarWidget, QDialog, QFormLayout,
    QDateTimeEdit, QSpinBox, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, QDate, QDateTime
from PyQt6.QtGui import QColor
from datetime import datetime, date, timedelta


class AppointmentWidget(QWidget):
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Calendar
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 8, 16)
        left_layout.setSpacing(12)

        left_header = QHBoxLayout()
        title = QLabel("Appointments")
        title.setObjectName("heading")
        left_header.addWidget(title)
        left_header.addStretch()

        new_btn = QPushButton("+ New Appointment")
        new_btn.setObjectName("primary_button")
        new_btn.setMinimumHeight(40)
        new_btn.clicked.connect(self.new_appointment_dialog)
        left_header.addWidget(new_btn)
        left_layout.addLayout(left_header)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMinimumHeight(300)
        self.calendar.selectionChanged.connect(self.on_date_selected)
        left_layout.addWidget(self.calendar)

        # Day's appointments
        day_title = QLabel("Selected Day")
        day_title.setObjectName("section_title")
        left_layout.addWidget(day_title)

        self.day_table = QTableWidget()
        self.day_table.setColumnCount(5)
        self.day_table.setHorizontalHeaderLabels(["Time", "Patient", "Type", "Status", "Reason"])
        self.day_table.horizontalHeader().setStretchLastSection(True)
        self.day_table.setAlternatingRowColors(True)
        self.day_table.verticalHeader().setVisible(False)
        self.day_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.day_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        left_layout.addWidget(self.day_table)

        splitter.addWidget(left)

        # Right: Full list
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 16, 16, 16)
        right_layout.setSpacing(12)

        right_header = QLabel("All Appointments")
        right_header.setObjectName("section_title")
        right_layout.addWidget(right_header)

        filter_row = QHBoxLayout()
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Scheduled", "Confirmed", "In Progress", "Completed", "Cancelled", "No Show"])
        self.status_filter.setMinimumHeight(38)
        self.status_filter.currentTextChanged.connect(self.refresh_data)
        filter_row.addWidget(self.status_filter)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Consultation", "Follow Up", "Procedure", "Psychiatric Eval", "Medication Review"])
        self.type_filter.setMinimumHeight(38)
        self.type_filter.currentTextChanged.connect(self.refresh_data)
        filter_row.addWidget(self.type_filter)
        right_layout.addLayout(filter_row)

        self.appt_table = QTableWidget()
        self.appt_table.setColumnCount(7)
        self.appt_table.setHorizontalHeaderLabels(["Date/Time", "Patient", "Provider", "Type", "Duration", "Status", "Reason"])
        self.appt_table.horizontalHeader().setStretchLastSection(True)
        self.appt_table.setAlternatingRowColors(True)
        self.appt_table.verticalHeader().setVisible(False)
        self.appt_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.appt_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.appt_table.doubleClicked.connect(self.on_appt_double_click)
        right_layout.addWidget(self.appt_table)

        # Action buttons
        action_row = QHBoxLayout()
        action_row.addStretch()
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setObjectName("success_button")
        confirm_btn.clicked.connect(lambda: self.update_status("confirmed"))
        action_row.addWidget(confirm_btn)

        start_btn = QPushButton("Start Visit")
        start_btn.setObjectName("primary_button")
        start_btn.clicked.connect(lambda: self.update_status("in_progress"))
        action_row.addWidget(start_btn)

        complete_btn = QPushButton("Complete")
        complete_btn.clicked.connect(lambda: self.update_status("completed"))
        action_row.addWidget(complete_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("danger_button")
        cancel_btn.clicked.connect(lambda: self.update_status("cancelled"))
        action_row.addWidget(cancel_btn)

        no_show_btn = QPushButton("No Show")
        no_show_btn.clicked.connect(lambda: self.update_status("no_show"))
        action_row.addWidget(no_show_btn)
        right_layout.addLayout(action_row)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self.all_appts = []

    def refresh_data(self):
        try:
            from_date = date.today() - timedelta(days=90)
            to_date = date.today() + timedelta(days=90)
            self.all_appts = self.db_manager.get_appointments(date_from=from_date, date_to=to_date)

            status_text = self.status_filter.currentText() if hasattr(self, "status_filter") else "All Status"
            type_text = self.type_filter.currentText() if hasattr(self, "type_filter") else "All Types"

            filtered = self.all_appts
            if status_text != "All Status":
                status_val = status_text.lower().replace(" ", "_")
                filtered = [a for a in filtered if a.get("status") == status_val]
            if type_text != "All Types":
                type_val = type_text.lower().replace(" ", "_")
                filtered = [a for a in filtered if a.get("appointment_type") == type_val]

            self.populate_main_table(filtered)
            self.on_date_selected()
        except Exception as e:
            print(f"Appointment refresh error: {e}")

    def populate_main_table(self, appts):
        status_colors = {
            "scheduled": QColor(3, 155, 229), "confirmed": QColor(67, 160, 71),
            "in_progress": QColor(251, 140, 0), "completed": QColor(128, 128, 128),
            "cancelled": QColor(229, 57, 53), "no_show": QColor(183, 28, 28)
        }
        self.appt_table.setRowCount(len(appts))
        for i, a in enumerate(appts):
            dt = a.get("scheduled_datetime", "")
            if dt:
                try:
                    t = datetime.fromisoformat(dt)
                    dt = t.strftime("%m/%d/%Y %I:%M %p")
                except (ValueError, TypeError):
                    pass
            self.appt_table.setItem(i, 0, QTableWidgetItem(str(dt)))
            self.appt_table.setItem(i, 1, QTableWidgetItem(a.get("patient_name", "")))
            self.appt_table.setItem(i, 2, QTableWidgetItem(a.get("provider_name", "")))
            self.appt_table.setItem(i, 3, QTableWidgetItem(a.get("appointment_type", "").replace("_", " ").title()))
            self.appt_table.setItem(i, 4, QTableWidgetItem(f"{a.get('duration_minutes', 30)} min"))

            status = a.get("status", "")
            status_item = QTableWidgetItem(status.replace("_", " ").title())
            color = status_colors.get(status, QColor(128, 128, 128))
            status_item.setForeground(color)
            self.appt_table.setItem(i, 5, status_item)

            self.appt_table.setItem(i, 6, QTableWidgetItem(a.get("reason", "")))

    def on_date_selected(self):
        selected = self.calendar.selectedDate().toPyDate()
        day_appts = []
        for a in self.all_appts:
            dt = a.get("scheduled_datetime", "")
            if dt:
                try:
                    t = datetime.fromisoformat(dt)
                    if t.date() == selected:
                        day_appts.append(a)
                except (ValueError, TypeError):
                    pass

        self.day_table.setRowCount(len(day_appts))
        for i, a in enumerate(day_appts):
            dt = a.get("scheduled_datetime", "")
            if dt:
                try:
                    t = datetime.fromisoformat(dt)
                    dt = t.strftime("%I:%M %p")
                except (ValueError, TypeError):
                    pass
            self.day_table.setItem(i, 0, QTableWidgetItem(str(dt)))
            self.day_table.setItem(i, 1, QTableWidgetItem(a.get("patient_name", "")))
            self.day_table.setItem(i, 2, QTableWidgetItem(a.get("appointment_type", "").replace("_", " ").title()))
            self.day_table.setItem(i, 3, QTableWidgetItem(a.get("status", "").replace("_", " ").title()))
            self.day_table.setItem(i, 4, QTableWidgetItem(a.get("reason", "")))

    def update_status(self, new_status):
        row = self.appt_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select an appointment.")
            return
        dt_item = self.appt_table.item(row, 0)
        patient_item = self.appt_table.item(row, 1)
        if not dt_item:
            return

        # Find the appointment
        for a in self.all_appts:
            if a.get("patient_name") == patient_item.text():
                try:
                    self.db_manager.update_appointment_status(a["id"], new_status)
                    self.refresh_data()
                    return
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))
                    return

    def on_appt_double_click(self, index):
        row = index.row()
        if row < 0:
            return
        patient = self.appt_table.item(row, 1)
        if patient:
            QMessageBox.information(self, "Appointment",
                f"Patient: {patient.text()}\n"
                f"Date: {self.appt_table.item(row, 0).text()}\n"
                f"Type: {self.appt_table.item(row, 3).text()}\n"
                f"Status: {self.appt_table.item(row, 5).text()}\n"
                f"Reason: {self.appt_table.item(row, 6).text()}")

    def new_appointment_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("New Appointment")
        dialog.setMinimumSize(500, 450)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        form.setSpacing(12)

        # Patient
        pat_search = QLineEdit()
        pat_search.setPlaceholderText("Search patient...")
        pat_search.setMinimumHeight(36)
        pat_combo = QComboBox()
        pat_combo.setMinimumHeight(36)
        def search_pat(text):
            pat_combo.clear()
            if len(text) >= 2:
                results = self.db_manager.search_patients(text)
                for p in results:
                    pat_combo.addItem(f"{p['full_name']} (ID: {p['id']})", p["id"])
        pat_search.textChanged.connect(search_pat)
        form.addRow("Search Patient:", pat_search)
        form.addRow("Patient:", pat_combo)

        # Provider
        prov_combo = QComboBox()
        prov_combo.setMinimumHeight(36)
        providers = self.db_manager.get_providers()
        for p in providers:
            prov_combo.addItem(f"{p['display_title']} ({p['specialization'] or ''})", p["id"])
        form.addRow("Provider:", prov_combo)

        # Type
        type_combo = QComboBox()
        type_combo.addItems(["consultation", "follow_up", "procedure", "psychiatric_eval", "medication_review"])
        type_combo.setMinimumHeight(36)
        form.addRow("Type:", type_combo)

        # DateTime
        dt_edit = QDateTimeEdit()
        dt_edit.setCalendarPopup(True)
        dt_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        dt_edit.setMinimumHeight(36)
        form.addRow("Date/Time:", dt_edit)

        # Duration
        dur_spin = QSpinBox()
        dur_spin.setRange(15, 120)
        dur_spin.setValue(30)
        dur_spin.setSuffix(" minutes")
        dur_spin.setMinimumHeight(36)
        form.addRow("Duration:", dur_spin)

        # Reason
        reason_edit = QLineEdit()
        reason_edit.setMinimumHeight(36)
        form.addRow("Reason:", reason_edit)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Schedule Appointment")
        save_btn.setObjectName("primary_button")
        save_btn.clicked.connect(lambda: self._save_appointment(
            dialog, pat_combo, prov_combo, type_combo, dt_edit, dur_spin, reason_edit))
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        dialog.exec()

    def _save_appointment(self, dialog, pat_combo, prov_combo, type_combo, dt_edit, dur_spin, reason_edit):
        patient_id = pat_combo.currentData()
        provider_id = prov_combo.currentData()
        if not patient_id:
            QMessageBox.warning(dialog, "Error", "Please select a patient.")
            return
        if not provider_id:
            QMessageBox.warning(dialog, "Error", "Please select a provider.")
            return
        try:
            from medical_erp.database.models import AppointmentType, AppointmentStatus
            self.db_manager.create_appointment(
                patient_id=patient_id,
                provider_id=provider_id,
                appointment_type=AppointmentType(type_combo.currentText()),
                scheduled_datetime=dt_edit.dateTime().toPyDateTime(),
                duration_minutes=dur_spin.value(),
                status=AppointmentStatus.SCHEDULED,
                reason=reason_edit.text().strip()
            )
            dialog.accept()
            self.refresh_data()
            QMessageBox.information(self, "Success", "Appointment scheduled.")
        except Exception as e:
            QMessageBox.warning(dialog, "Error", str(e))
