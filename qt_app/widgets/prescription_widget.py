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
MedPharm ERP - Prescription Management Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QSplitter, QDialog, QFormLayout, QSpinBox,
    QTextEdit, QScrollArea, QGroupBox, QListWidget, QListWidgetItem,
    QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor


class PrescriptionWidget(QWidget):
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Prescriptions")
        title.setObjectName("heading")
        header_row.addWidget(title)
        header_row.addStretch()

        new_btn = QPushButton("+ New Prescription")
        new_btn.setObjectName("primary_button")
        new_btn.setMinimumHeight(40)
        new_btn.clicked.connect(self.new_prescription_dialog)
        header_row.addWidget(new_btn)
        layout.addLayout(header_row)

        # Filters
        filter_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by patient or Rx#...")
        self.search_input.setMinimumHeight(38)
        self.search_input.textChanged.connect(self.apply_filter)
        filter_row.addWidget(self.search_input, 3)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Active", "Pending", "Filled", "Expired", "Cancelled"])
        self.status_filter.setMinimumHeight(38)
        self.status_filter.currentTextChanged.connect(self.refresh_data)
        filter_row.addWidget(self.status_filter, 1)
        layout.addLayout(filter_row)

        # Table
        self.rx_table = QTableWidget()
        self.rx_table.setColumnCount(7)
        self.rx_table.setHorizontalHeaderLabels(["Rx#", "Patient", "Prescriber", "Date", "Status", "Medications", "Total"])
        self.rx_table.horizontalHeader().setStretchLastSection(True)
        self.rx_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rx_table.setAlternatingRowColors(True)
        self.rx_table.verticalHeader().setVisible(False)
        self.rx_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.rx_table.doubleClicked.connect(self.view_prescription_detail)
        self.rx_table.setColumnWidth(0, 120)
        self.rx_table.setColumnWidth(1, 150)
        self.rx_table.setColumnWidth(2, 130)
        self.rx_table.setColumnWidth(3, 100)
        self.rx_table.setColumnWidth(4, 90)
        self.rx_table.setColumnWidth(6, 90)
        layout.addWidget(self.rx_table)

        self.all_prescriptions = []

    def refresh_data(self):
        try:
            status_text = self.status_filter.currentText() if hasattr(self, "status_filter") else "All Status"
            status = None if status_text == "All Status" else status_text.lower()
            self.all_prescriptions = self.db_manager.get_all_prescriptions(status)
            self.apply_filter()
        except Exception as e:
            print(f"Prescription refresh error: {e}")

    def apply_filter(self):
        search = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        rxs = self.all_prescriptions
        if search:
            rxs = [r for r in rxs if
                   search in r.get("rx_number", "").lower() or
                   search in r.get("patient_name", "").lower() or
                   search in r.get("prescriber_name", "").lower()]
        self.populate_table(rxs)

    def populate_table(self, rxs):
        status_colors = {
            "active": QColor(67, 160, 71), "pending": QColor(251, 140, 0),
            "filled": QColor(3, 155, 229), "expired": QColor(229, 57, 53),
            "cancelled": QColor(128, 128, 128)
        }
        self.rx_table.setRowCount(len(rxs))
        for i, rx in enumerate(rxs):
            self.rx_table.setItem(i, 0, QTableWidgetItem(rx.get("rx_number", "")))
            self.rx_table.setItem(i, 1, QTableWidgetItem(rx.get("patient_name", "")))
            self.rx_table.setItem(i, 2, QTableWidgetItem(rx.get("prescriber_name", "")))
            self.rx_table.setItem(i, 3, QTableWidgetItem(rx.get("prescribed_date", "")))

            status = rx.get("status", "")
            status_item = QTableWidgetItem(status.title())
            color = status_colors.get(status, QColor(128, 128, 128))
            status_item.setForeground(color)
            self.rx_table.setItem(i, 4, status_item)

            meds = ", ".join(item["medication_name"] for item in rx.get("items", []))
            self.rx_table.setItem(i, 5, QTableWidgetItem(meds))
            self.rx_table.setItem(i, 6, QTableWidgetItem(f"${rx.get('total', 0):.2f}"))

    def view_prescription_detail(self, index):
        row = index.row()
        rx_num_item = self.rx_table.item(row, 0)
        if not rx_num_item:
            return
        rx_num = rx_num_item.text()
        rx = next((r for r in self.all_prescriptions if r["rx_number"] == rx_num), None)
        if not rx:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Prescription {rx_num}")
        dialog.setMinimumSize(650, 550)
        layout = QVBoxLayout(dialog)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        clayout = QVBoxLayout(content)
        clayout.setSpacing(12)

        # Header info
        info = QGroupBox("Prescription Information")
        info_layout = QFormLayout(info)
        info_layout.addRow("Rx Number:", QLabel(rx["rx_number"]))
        info_layout.addRow("Patient:", QLabel(rx["patient_name"]))
        info_layout.addRow("Prescriber:", QLabel(rx["prescriber_name"]))
        info_layout.addRow("Status:", QLabel(rx["status"].title()))
        info_layout.addRow("Prescribed:", QLabel(rx.get("prescribed_date", "")))
        info_layout.addRow("Expires:", QLabel(rx.get("expiry_date", "")))
        if rx.get("diagnosis"):
            info_layout.addRow("Diagnosis:", QLabel(rx["diagnosis"]))
        clayout.addWidget(info)

        # Items
        items_group = QGroupBox("Medications")
        items_layout = QVBoxLayout(items_group)
        for item in rx.get("items", []):
            item_frame = QFrame()
            item_frame.setObjectName("card")
            il = QVBoxLayout(item_frame)
            med_name = QLabel(f"{item['medication_name']} ({item.get('generic_name', '')})")
            med_name.setStyleSheet("font-weight: bold; font-size: 14px; color: #00BCD4;")
            il.addWidget(med_name)
            il.addWidget(QLabel(f"Dosage: {item['dosage']}  |  Frequency: {item['frequency']}  |  Duration: {item.get('duration', 'N/A')}"))
            il.addWidget(QLabel(f"Quantity: {item['quantity']}  |  Refills: {item['refills_used']}/{item['refills_allowed']}"))
            if item.get("instructions"):
                il.addWidget(QLabel(f"Instructions: {item['instructions']}"))
            il.addWidget(QLabel(f"Cost: ${item.get('total_price', 0):.2f}"))
            items_layout.addWidget(item_frame)
        clayout.addWidget(items_group)

        # Total
        total_label = QLabel(f"Total: ${rx.get('total', 0):.2f}")
        total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00BCD4;")
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        clayout.addWidget(total_label)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Actions
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        if rx["status"] == "active":
            cancel_btn = QPushButton("Cancel Prescription")
            cancel_btn.setObjectName("danger_button")
            cancel_btn.clicked.connect(lambda: self._cancel_rx(rx["id"], dialog))
            btn_row.addWidget(cancel_btn)

            bill_btn = QPushButton("Generate Invoice")
            bill_btn.setObjectName("primary_button")
            bill_btn.clicked.connect(lambda: self._generate_invoice(rx["id"], dialog))
            btn_row.addWidget(bill_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
        dialog.exec()

    def _cancel_rx(self, rx_id, dialog):
        reply = QMessageBox.question(dialog, "Confirm", "Cancel this prescription?")
        if reply == QMessageBox.StandardButton.Yes:
            self.db_manager.update_prescription_status(rx_id, "cancelled")
            dialog.accept()
            self.refresh_data()

    def _generate_invoice(self, rx_id, dialog):
        try:
            inv_id = self.db_manager.create_invoice_from_prescription(rx_id)
            if inv_id:
                QMessageBox.information(dialog, "Success", "Invoice generated successfully.")
            else:
                QMessageBox.warning(dialog, "Error", "Failed to generate invoice.")
        except Exception as e:
            QMessageBox.warning(dialog, "Error", str(e))

    def new_prescription_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("New Prescription")
        dialog.setMinimumSize(700, 650)
        layout = QVBoxLayout(dialog)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        clayout = QVBoxLayout(content)
        clayout.setSpacing(12)

        # Patient selection
        pat_group = QGroupBox("Patient")
        pat_layout = QHBoxLayout(pat_group)
        pat_search = QLineEdit()
        pat_search.setPlaceholderText("Search patient...")
        pat_search.setMinimumHeight(36)
        pat_layout.addWidget(pat_search)
        pat_combo = QComboBox()
        pat_combo.setMinimumHeight(36)
        pat_combo.setMinimumWidth(250)
        pat_layout.addWidget(pat_combo)
        clayout.addWidget(pat_group)

        def search_pat(text):
            pat_combo.clear()
            if len(text) >= 2:
                results = self.db_manager.search_patients(text)
                for p in results:
                    pat_combo.addItem(f"{p['full_name']} (ID: {p['id']})", p["id"])
        pat_search.textChanged.connect(search_pat)

        # Medications
        med_group = QGroupBox("Medications")
        med_layout = QVBoxLayout(med_group)

        med_items = []

        def add_med_row():
            row_frame = QFrame()
            row_frame.setObjectName("card")
            rl = QVBoxLayout(row_frame)

            r1 = QHBoxLayout()
            med_search = QLineEdit()
            med_search.setPlaceholderText("Search medication...")
            med_search.setMinimumHeight(36)
            r1.addWidget(med_search, 2)
            med_combo = QComboBox()
            med_combo.setMinimumHeight(36)
            r1.addWidget(med_combo, 3)
            rl.addLayout(r1)

            def search_med(text):
                med_combo.clear()
                if len(text) >= 2:
                    results = self.db_manager.search_medications(text)
                    for m in results:
                        med_combo.addItem(
                            f"{m['brand_name']} ({m['generic_name']}) {m['strength']} - ${m['retail_price']:.2f}",
                            m["id"]
                        )
            med_search.textChanged.connect(search_med)

            r2 = QHBoxLayout()
            dosage = QLineEdit()
            dosage.setPlaceholderText("Dosage")
            dosage.setMinimumHeight(36)
            r2.addWidget(dosage)
            freq = QComboBox()
            freq.addItems(["Once daily", "Twice daily", "Three times daily",
                           "Four times daily", "Every 4-6 hours PRN",
                           "Every 8 hours", "Every 12 hours", "At bedtime",
                           "As directed"])
            freq.setMinimumHeight(36)
            r2.addWidget(freq)
            qty = QSpinBox()
            qty.setRange(1, 999)
            qty.setValue(30)
            qty.setMinimumHeight(36)
            qty.setPrefix("Qty: ")
            r2.addWidget(qty)
            refills = QSpinBox()
            refills.setRange(0, 12)
            refills.setMinimumHeight(36)
            refills.setPrefix("Refills: ")
            r2.addWidget(refills)
            rl.addLayout(r2)

            instructions = QLineEdit()
            instructions.setPlaceholderText("Special instructions...")
            instructions.setMinimumHeight(36)
            rl.addWidget(instructions)

            med_layout.addWidget(row_frame)
            med_items.append({
                "combo": med_combo, "dosage": dosage, "frequency": freq,
                "quantity": qty, "refills": refills, "instructions": instructions
            })

        add_med_row()

        add_med_btn = QPushButton("+ Add Another Medication")
        add_med_btn.clicked.connect(add_med_row)
        med_layout.addWidget(add_med_btn)
        clayout.addWidget(med_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        notes_edit = QTextEdit()
        notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(notes_edit)
        clayout.addWidget(notes_group)

        # Interaction check
        self.interaction_label = QLabel("")
        self.interaction_label.setWordWrap(True)
        clayout.addWidget(self.interaction_label)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        check_btn = QPushButton("Check Interactions")
        check_btn.setObjectName("warning_button")
        check_btn.clicked.connect(lambda: self._check_interactions(med_items))
        btn_row.addWidget(check_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Create Prescription")
        save_btn.setObjectName("primary_button")
        save_btn.clicked.connect(lambda: self._save_prescription(dialog, pat_combo, med_items, notes_edit))
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        dialog.exec()

    def _check_interactions(self, med_items):
        med_ids = []
        for mi in med_items:
            mid = mi["combo"].currentData()
            if mid:
                med_ids.append(mid)
        if len(med_ids) < 2:
            self.interaction_label.setText("Add at least 2 medications to check interactions.")
            self.interaction_label.setStyleSheet("color: #808080;")
            return
        interactions = self.db_manager.check_interactions(med_ids)
        if not interactions:
            self.interaction_label.setText("No known interactions found.")
            self.interaction_label.setStyleSheet("color: #43A047; font-weight: bold;")
        else:
            msgs = []
            for inter in interactions:
                sev = inter["severity"].upper()
                msgs.append(f"[{sev}] {inter['medication_a']} + {inter['medication_b']}: {inter['description']}")
            self.interaction_label.setText("\n\n".join(msgs))
            self.interaction_label.setStyleSheet("color: #E53935; font-weight: bold;")

    def _save_prescription(self, dialog, pat_combo, med_items, notes_edit):
        patient_id = pat_combo.currentData()
        if not patient_id:
            QMessageBox.warning(dialog, "Error", "Please select a patient.")
            return
        items = []
        for mi in med_items:
            mid = mi["combo"].currentData()
            if not mid:
                continue
            dosage = mi["dosage"].text().strip()
            if not dosage:
                QMessageBox.warning(dialog, "Error", "Please enter dosage for all medications.")
                return
            items.append({
                "medication_id": mid,
                "dosage": dosage,
                "frequency": mi["frequency"].currentText(),
                "quantity": mi["quantity"].value(),
                "refills_allowed": mi["refills"].value(),
                "instructions": mi["instructions"].text().strip(),
            })
        if not items:
            QMessageBox.warning(dialog, "Error", "Please add at least one medication.")
            return
        try:
            self.db_manager.create_prescription(
                patient_id=patient_id,
                prescriber_id=self.current_user.get("id", 1),
                items=items,
                notes=notes_edit.toPlainText().strip()
            )
            dialog.accept()
            self.refresh_data()
            QMessageBox.information(self, "Success", "Prescription created successfully.")
        except Exception as e:
            QMessageBox.warning(dialog, "Error", f"Failed to create prescription: {e}")
