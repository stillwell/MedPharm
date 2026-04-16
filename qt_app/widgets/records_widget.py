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
MedPharm ERP - Medical Records Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QSplitter, QTextEdit, QDialog, QFormLayout,
    QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class RecordsWidget(QWidget):
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.selected_patient_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Medical Records")
        title.setObjectName("heading")
        header_row.addWidget(title)
        header_row.addStretch()

        new_btn = QPushButton("+ New Record")
        new_btn.setObjectName("primary_button")
        new_btn.setMinimumHeight(40)
        new_btn.clicked.connect(self.new_record_dialog)
        header_row.addWidget(new_btn)
        layout.addLayout(header_row)

        # Patient search + type filter
        filter_row = QHBoxLayout()
        pat_search = QLineEdit()
        pat_search.setPlaceholderText("Search patient...")
        pat_search.setMinimumHeight(38)
        filter_row.addWidget(pat_search, 1)

        self.pat_combo = QComboBox()
        self.pat_combo.setMinimumHeight(38)
        self.pat_combo.setMinimumWidth(250)
        self.pat_combo.currentIndexChanged.connect(self.on_patient_changed)
        filter_row.addWidget(self.pat_combo, 2)

        def search_p(text):
            self.pat_combo.clear()
            self.pat_combo.addItem("-- Select Patient --", None)
            if len(text) >= 2:
                results = self.db_manager.search_patients(text)
                for p in results:
                    self.pat_combo.addItem(f"{p['full_name']} (ID: {p['id']})", p["id"])
        pat_search.textChanged.connect(search_p)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Visit Notes", "Lab Results", "Imaging", "Procedures", "Referrals", "Other"])
        self.type_filter.setMinimumHeight(38)
        self.type_filter.currentTextChanged.connect(self.load_records)
        filter_row.addWidget(self.type_filter, 1)
        layout.addLayout(filter_row)

        # Content area
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Records list
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(4)
        self.records_table.setHorizontalHeaderLabels(["Date", "Type", "Title", "Provider"])
        self.records_table.horizontalHeader().setStretchLastSection(True)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.verticalHeader().setVisible(False)
        self.records_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.records_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.records_table.currentCellChanged.connect(self.on_record_selected)
        self.records_table.setColumnWidth(0, 100)
        self.records_table.setColumnWidth(1, 100)
        self.records_table.setColumnWidth(2, 250)
        splitter.addWidget(self.records_table)

        # Detail view
        detail_frame = QFrame()
        detail_frame.setObjectName("card")
        detail_layout = QVBoxLayout(detail_frame)

        self.detail_title = QLabel("Select a record to view")
        self.detail_title.setObjectName("section_title")
        detail_layout.addWidget(self.detail_title)

        self.detail_meta = QLabel("")
        self.detail_meta.setStyleSheet("color: #808080; font-size: 12px;")
        detail_layout.addWidget(self.detail_meta)

        self.detail_content = QTextEdit()
        self.detail_content.setReadOnly(True)
        detail_layout.addWidget(self.detail_content)

        splitter.addWidget(detail_frame)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self.all_records = []

    def refresh_data(self):
        if self.selected_patient_id:
            self.load_records()

    def on_patient_changed(self, index):
        pid = self.pat_combo.currentData()
        if pid:
            self.selected_patient_id = pid
            self.load_records()
        else:
            self.selected_patient_id = None
            self.records_table.setRowCount(0)
            self.detail_title.setText("Select a patient to view records")
            self.detail_content.clear()

    def load_records(self):
        if not self.selected_patient_id:
            return
        try:
            type_text = self.type_filter.currentText()
            type_map = {
                "Visit Notes": "visit_note", "Lab Results": "lab_result",
                "Imaging": "imaging", "Procedures": "procedure",
                "Referrals": "referral", "Other": "other"
            }
            record_type = type_map.get(type_text)
            self.all_records = self.db_manager.get_patient_records(
                self.selected_patient_id, record_type)
            self.populate_table()
        except Exception as e:
            print(f"Records load error: {e}")

    def populate_table(self):
        type_colors = {
            "visit_note": QColor(3, 155, 229), "lab_result": QColor(67, 160, 71),
            "imaging": QColor(124, 77, 255), "procedure": QColor(251, 140, 0),
            "referral": QColor(229, 57, 53), "other": QColor(128, 128, 128)
        }
        self.records_table.setRowCount(len(self.all_records))
        for i, r in enumerate(self.all_records):
            self.records_table.setItem(i, 0, QTableWidgetItem(r.get("record_date", "")))
            rtype = r.get("record_type", "")
            type_item = QTableWidgetItem(rtype.replace("_", " ").title())
            color = type_colors.get(rtype, QColor(128, 128, 128))
            type_item.setForeground(color)
            self.records_table.setItem(i, 1, type_item)
            self.records_table.setItem(i, 2, QTableWidgetItem(r.get("title", "")))
            self.records_table.setItem(i, 3, QTableWidgetItem(r.get("provider", "")))

    def on_record_selected(self, row, col, prev_row, prev_col):
        if row < 0 or row >= len(self.all_records):
            return
        record = self.all_records[row]
        self.detail_title.setText(record.get("title", ""))
        self.detail_meta.setText(
            f"Type: {record.get('record_type', '').replace('_', ' ').title()}  |  "
            f"Date: {record.get('record_date', '')}  |  "
            f"Provider: {record.get('provider', '')}"
        )
        self.detail_content.setPlainText(record.get("content", ""))

    def new_record_dialog(self):
        if not self.selected_patient_id:
            QMessageBox.warning(self, "Error", "Please select a patient first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("New Medical Record")
        dialog.setMinimumSize(600, 500)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        form.setSpacing(12)

        type_combo = QComboBox()
        type_combo.addItems(["visit_note", "lab_result", "imaging", "procedure", "referral", "other"])
        type_combo.setMinimumHeight(36)
        form.addRow("Type:", type_combo)

        title_edit = QLineEdit()
        title_edit.setMinimumHeight(36)
        title_edit.setPlaceholderText("Record title...")
        form.addRow("Title:", title_edit)

        content_edit = QTextEdit()
        content_edit.setPlaceholderText("Enter record content...")
        form.addRow("Content:", content_edit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Record")
        save_btn.setObjectName("primary_button")
        save_btn.clicked.connect(lambda: self._save_record(
            dialog, type_combo, title_edit, content_edit))
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        dialog.exec()

    def _save_record(self, dialog, type_combo, title_edit, content_edit):
        title = title_edit.text().strip()
        if not title:
            QMessageBox.warning(dialog, "Error", "Title is required.")
            return
        try:
            from database.models import RecordType
            self.db_manager.add_medical_record(
                patient_id=self.selected_patient_id,
                provider_id=self.current_user.get("id", 1),
                record_type=RecordType(type_combo.currentText()),
                title=title,
                content=content_edit.toPlainText().strip()
            )
            dialog.accept()
            self.load_records()
            QMessageBox.information(self, "Success", "Medical record saved.")
        except Exception as e:
            QMessageBox.warning(dialog, "Error", str(e))
