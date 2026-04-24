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
MedPharm ERP - Patient Management Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QFormLayout, QComboBox, QDateEdit, QTextEdit, QMessageBox,
    QSplitter, QDialog, QScrollArea, QGroupBox, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import date


class PatientWidget(QWidget):
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.selected_patient_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left Panel: Search + List ──
        left = QFrame()
        left.setMaximumWidth(500)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 8, 16)
        left_layout.setSpacing(12)

        title = QLabel("Patients")
        title.setObjectName("heading")
        left_layout.addWidget(title)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, email, or phone...")
        self.search_input.textChanged.connect(self.search_patients)
        self.search_input.setMinimumHeight(38)
        search_row.addWidget(self.search_input)

        add_btn = QPushButton("+ New Patient")
        add_btn.setObjectName("primary_button")
        add_btn.setMinimumHeight(38)
        add_btn.clicked.connect(self.add_patient_dialog)
        search_row.addWidget(add_btn)
        left_layout.addLayout(search_row)

        self.patient_table = QTableWidget()
        self.patient_table.setColumnCount(5)
        self.patient_table.setHorizontalHeaderLabels(["ID", "Name", "DOB", "Phone", "Status"])
        self.patient_table.horizontalHeader().setStretchLastSection(True)
        self.patient_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.patient_table.setAlternatingRowColors(True)
        self.patient_table.verticalHeader().setVisible(False)
        self.patient_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.patient_table.currentCellChanged.connect(self.on_patient_selected)
        self.patient_table.setColumnWidth(0, 50)
        self.patient_table.setColumnWidth(1, 160)
        self.patient_table.setColumnWidth(2, 100)
        self.patient_table.setColumnWidth(3, 110)
        left_layout.addWidget(self.patient_table)

        splitter.addWidget(left)

        # ── Right Panel: Detail Tabs ──
        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 16, 16, 16)
        right_layout.setSpacing(12)

        self.detail_header = QLabel("Select a patient")
        self.detail_header.setObjectName("heading")
        right_layout.addWidget(self.detail_header)

        self.tabs = QTabWidget()

        # Demographics tab
        self.demo_tab = QScrollArea()
        self.demo_tab.setWidgetResizable(True)
        self.demo_tab.setFrameShape(QFrame.Shape.NoFrame)
        demo_widget = QWidget()
        self.demo_form = QFormLayout(demo_widget)
        self.demo_form.setSpacing(10)
        self.demo_form.setContentsMargins(16, 16, 16, 16)
        self.demo_fields = {}
        for field in ["First Name", "Last Name", "Date of Birth", "Gender", "Email",
                       "Phone", "Address", "City", "State", "Zip Code",
                       "Emergency Contact", "Emergency Phone", "Blood Type"]:
            label = QLabel(field)
            label.setStyleSheet("color: #808080; font-size: 12px;")
            value = QLabel("-")
            value.setStyleSheet("font-size: 14px; font-weight: 500;")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.demo_form.addRow(label, value)
            self.demo_fields[field] = value
        self.demo_tab.setWidget(demo_widget)
        self.tabs.addTab(self.demo_tab, "Demographics")

        # Insurance tab
        self.insurance_table = QTableWidget()
        self.insurance_table.setColumnCount(5)
        self.insurance_table.setHorizontalHeaderLabels(["Provider", "Policy #", "Group #", "Copay", "Type"])
        self.insurance_table.horizontalHeader().setStretchLastSection(True)
        self.insurance_table.setAlternatingRowColors(True)
        self.insurance_table.verticalHeader().setVisible(False)
        self.insurance_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.insurance_table, "Insurance")

        # Allergies tab
        self.allergy_table = QTableWidget()
        self.allergy_table.setColumnCount(3)
        self.allergy_table.setHorizontalHeaderLabels(["Allergen", "Reaction", "Severity"])
        self.allergy_table.horizontalHeader().setStretchLastSection(True)
        self.allergy_table.setAlternatingRowColors(True)
        self.allergy_table.verticalHeader().setVisible(False)
        self.allergy_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.allergy_table, "Allergies")

        # Vitals tab
        self.vitals_table = QTableWidget()
        self.vitals_table.setColumnCount(8)
        self.vitals_table.setHorizontalHeaderLabels(["Date", "BP", "HR", "Temp", "RR", "SpO2", "Weight", "BMI"])
        self.vitals_table.horizontalHeader().setStretchLastSection(True)
        self.vitals_table.setAlternatingRowColors(True)
        self.vitals_table.verticalHeader().setVisible(False)
        self.vitals_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.vitals_table, "Vitals")

        # Diagnoses tab
        self.dx_table = QTableWidget()
        self.dx_table.setColumnCount(5)
        self.dx_table.setHorizontalHeaderLabels(["ICD-10", "Description", "Status", "Date", "Provider"])
        self.dx_table.horizontalHeader().setStretchLastSection(True)
        self.dx_table.setAlternatingRowColors(True)
        self.dx_table.verticalHeader().setVisible(False)
        self.dx_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.dx_table, "Diagnoses")

        # Prescriptions tab
        self.rx_table = QTableWidget()
        self.rx_table.setColumnCount(5)
        self.rx_table.setHorizontalHeaderLabels(["Rx#", "Medications", "Status", "Date", "Prescriber"])
        self.rx_table.horizontalHeader().setStretchLastSection(True)
        self.rx_table.setAlternatingRowColors(True)
        self.rx_table.verticalHeader().setVisible(False)
        self.rx_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.rx_table, "Prescriptions")

        # Billing tab
        self.billing_table = QTableWidget()
        self.billing_table.setColumnCount(5)
        self.billing_table.setHorizontalHeaderLabels(["Invoice#", "Date", "Total", "Paid", "Status"])
        self.billing_table.horizontalHeader().setStretchLastSection(True)
        self.billing_table.setAlternatingRowColors(True)
        self.billing_table.verticalHeader().setVisible(False)
        self.billing_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.billing_table, "Billing")

        # Notes tab — private, author-only
        self._build_notes_tab()

        right_layout.addWidget(self.tabs)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

    def refresh_data(self):
        self.search_patients("")

    def search_patients(self, query=""):
        q = self.search_input.text().strip() if not query and hasattr(self, "search_input") else query
        try:
            patients = self.db_manager.search_patients(q)
            self.patient_table.setRowCount(len(patients))
            for i, p in enumerate(patients):
                self.patient_table.setItem(i, 0, QTableWidgetItem(str(p["id"])))
                self.patient_table.setItem(i, 1, QTableWidgetItem(p["full_name"]))
                self.patient_table.setItem(i, 2, QTableWidgetItem(p.get("dob", "")))
                self.patient_table.setItem(i, 3, QTableWidgetItem(p.get("phone", "")))
                status = "Active" if p.get("is_active") else "Inactive"
                item = QTableWidgetItem(status)
                if status == "Active":
                    item.setForeground(Qt.GlobalColor.green)
                self.patient_table.setItem(i, 4, item)
        except Exception as e:
            print(f"Patient search error: {e}")

    def on_patient_selected(self, row, col, prev_row, prev_col):
        if row < 0:
            return
        id_item = self.patient_table.item(row, 0)
        if not id_item:
            return
        pid = int(id_item.text())
        self.selected_patient_id = pid
        self.load_patient_details(pid)

    def load_patient_details(self, patient_id):
        try:
            p = self.db_manager.get_patient_full(patient_id)
            if not p:
                return
            self.detail_header.setText(f"{p['full_name']} (ID: {p['id']})")

            # Demographics
            self.demo_fields["First Name"].setText(p.get("first_name", "-"))
            self.demo_fields["Last Name"].setText(p.get("last_name", "-"))
            self.demo_fields["Date of Birth"].setText(f"{p.get('dob', '-')} (Age: {p.get('age', '?')})")
            self.demo_fields["Gender"].setText((p.get("gender") or "-").title())
            self.demo_fields["Email"].setText(p.get("email") or "-")
            self.demo_fields["Phone"].setText(p.get("phone") or "-")
            self.demo_fields["Address"].setText(p.get("address") or "-")
            self.demo_fields["City"].setText(p.get("city") or "-")
            self.demo_fields["State"].setText(p.get("state") or "-")
            self.demo_fields["Zip Code"].setText(p.get("zip_code") or "-")
            self.demo_fields["Emergency Contact"].setText(p.get("emergency_contact_name") or "-")
            self.demo_fields["Emergency Phone"].setText(p.get("emergency_contact_phone") or "-")
            self.demo_fields["Blood Type"].setText(p.get("blood_type") or "-")

            # Insurance
            ins_records = p.get("insurance_records", [])
            self.insurance_table.setRowCount(len(ins_records))
            for i, ins in enumerate(ins_records):
                self.insurance_table.setItem(i, 0, QTableWidgetItem(ins.get("provider_name", "")))
                self.insurance_table.setItem(i, 1, QTableWidgetItem(ins.get("policy_number", "")))
                self.insurance_table.setItem(i, 2, QTableWidgetItem(ins.get("group_number") or ""))
                self.insurance_table.setItem(i, 3, QTableWidgetItem(f"${ins.get('copay_amount', 0):.2f}"))
                self.insurance_table.setItem(i, 4, QTableWidgetItem(ins.get("coverage_type") or ""))

            # Allergies
            allergies = p.get("allergies", [])
            self.allergy_table.setRowCount(len(allergies))
            severity_colors = {"mild": "#43A047", "moderate": "#FB8C00", "severe": "#E53935", "life_threatening": "#B71C1C"}
            for i, a in enumerate(allergies):
                self.allergy_table.setItem(i, 0, QTableWidgetItem(a.get("allergen", "")))
                self.allergy_table.setItem(i, 1, QTableWidgetItem(a.get("reaction", "")))
                sev = a.get("severity", "")
                item = QTableWidgetItem(sev.replace("_", " ").title())
                self.allergy_table.setItem(i, 2, item)

            # Vitals
            vitals = self.db_manager.get_patient_vitals(patient_id)
            self.vitals_table.setRowCount(len(vitals))
            for i, v in enumerate(vitals):
                dt = v.get("recorded_at", "")
                if dt:
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(dt).strftime("%m/%d/%Y %H:%M")
                    except (ValueError, TypeError):
                        pass
                self.vitals_table.setItem(i, 0, QTableWidgetItem(str(dt)))
                bp_s, bp_d = v.get("bp_systolic"), v.get("bp_diastolic")
                bp = f"{bp_s}/{bp_d}" if bp_s and bp_d else "-"
                self.vitals_table.setItem(i, 1, QTableWidgetItem(bp))
                self.vitals_table.setItem(i, 2, QTableWidgetItem(str(v.get("heart_rate") or "-")))
                self.vitals_table.setItem(i, 3, QTableWidgetItem(str(v.get("temperature") or "-")))
                self.vitals_table.setItem(i, 4, QTableWidgetItem(str(v.get("respiratory_rate") or "-")))
                self.vitals_table.setItem(i, 5, QTableWidgetItem(str(v.get("oxygen_saturation") or "-")))
                self.vitals_table.setItem(i, 6, QTableWidgetItem(str(v.get("weight") or "-")))
                self.vitals_table.setItem(i, 7, QTableWidgetItem(str(v.get("bmi") or "-")))

            # Diagnoses
            dxs = p.get("diagnoses", [])
            self.dx_table.setRowCount(len(dxs))
            for i, d in enumerate(dxs):
                self.dx_table.setItem(i, 0, QTableWidgetItem(d.get("icd10_code", "")))
                self.dx_table.setItem(i, 1, QTableWidgetItem(d.get("description", "")))
                self.dx_table.setItem(i, 2, QTableWidgetItem(d.get("status", "").title()))
                self.dx_table.setItem(i, 3, QTableWidgetItem(d.get("diagnosis_date", "")))
                self.dx_table.setItem(i, 4, QTableWidgetItem(d.get("diagnosed_by", "")))

            # Prescriptions
            rxs = self.db_manager.get_prescriptions_by_patient(patient_id)
            self.rx_table.setRowCount(len(rxs))
            for i, rx in enumerate(rxs):
                self.rx_table.setItem(i, 0, QTableWidgetItem(rx.get("rx_number", "")))
                meds = ", ".join(item["medication_name"] for item in rx.get("items", []))
                self.rx_table.setItem(i, 1, QTableWidgetItem(meds))
                self.rx_table.setItem(i, 2, QTableWidgetItem(rx.get("status", "").title()))
                self.rx_table.setItem(i, 3, QTableWidgetItem(rx.get("prescribed_date", "")))
                self.rx_table.setItem(i, 4, QTableWidgetItem(rx.get("prescriber_name", "")))

            # Billing
            invs = self.db_manager.get_patient_invoices(patient_id)
            self.billing_table.setRowCount(len(invs))
            for i, inv in enumerate(invs):
                self.billing_table.setItem(i, 0, QTableWidgetItem(inv.get("invoice_number", "")))
                self.billing_table.setItem(i, 1, QTableWidgetItem(inv.get("invoice_date", "")))
                self.billing_table.setItem(i, 2, QTableWidgetItem(f"${inv.get('total_amount', 0):.2f}"))
                self.billing_table.setItem(i, 3, QTableWidgetItem(f"${inv.get('amount_paid', 0):.2f}"))
                self.billing_table.setItem(i, 4, QTableWidgetItem(inv.get("status", "").title()))

            self.load_notes(patient_id)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load patient details: {e}")

    # ── Private notes tab ────────────────────────────────────────────────

    def _build_notes_tab(self):
        tab = QWidget()
        tl = QVBoxLayout(tab)
        tl.setContentsMargins(8, 8, 8, 8)

        hint = QLabel(
            "Private notes are visible only to you. They are encrypted at "
            "rest and are not shared with other clinicians or the patient.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #90A4AE; font-size: 11px; padding: 4px 0;")
        tl.addWidget(hint)

        action_row = QHBoxLayout()
        add_btn = QPushButton("+ New Note")
        add_btn.setObjectName("primary_button")
        add_btn.clicked.connect(self.new_note_dialog)
        action_row.addWidget(add_btn)
        action_row.addStretch()
        tl.addLayout(action_row)

        self.notes_scroll = QScrollArea()
        self.notes_scroll.setWidgetResizable(True)
        self.notes_container = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_container)
        self.notes_layout.setSpacing(8)
        self.notes_layout.addStretch()
        self.notes_scroll.setWidget(self.notes_container)
        tl.addWidget(self.notes_scroll, 1)

        self.tabs.addTab(tab, "Notes")

    def load_notes(self, patient_id: int):
        author_id = self.current_user.get("id") if self.current_user else None
        if not author_id:
            return
        while self.notes_layout.count() > 1:
            item = self.notes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        try:
            notes = self.db_manager.list_provider_notes(
                patient_id=patient_id, author_id=author_id)
        except Exception as e:
            print(f"notes load error: {e}")
            return
        if not notes:
            empty = QLabel("No private notes yet.")
            empty.setStyleSheet("color: #808080; padding: 16px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.notes_layout.insertWidget(0, empty)
            return
        for n in notes:
            self.notes_layout.insertWidget(
                self.notes_layout.count() - 1, self._note_card(n))

    def _note_card(self, note: dict) -> QFrame:
        from datetime import datetime as _dt
        frame = QFrame()
        border = "#E65100" if note.get("is_pinned") else "#455A64"
        frame.setStyleSheet(
            f"background-color: #2A2D35; border-radius: 8px; "
            f"border-left: 3px solid {border};")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 10, 12, 10)

        head = QHBoxLayout()
        updated = note.get("updated_at") or note.get("created_at") or ""
        try:
            updated = _dt.fromisoformat(updated).strftime("%Y-%m-%d %H:%M")
        except (TypeError, ValueError):
            pass
        label = QLabel(
            f"{'📌 ' if note.get('is_pinned') else ''}Updated {updated}")
        label.setStyleSheet("color: #90A4AE; font-size: 11px;")
        head.addWidget(label)
        head.addStretch()
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedWidth(60)
        edit_btn.clicked.connect(lambda: self.edit_note_dialog(note))
        head.addWidget(edit_btn)
        del_btn = QPushButton("Delete")
        del_btn.setFixedWidth(70)
        del_btn.clicked.connect(lambda: self.delete_note(note))
        head.addWidget(del_btn)
        lay.addLayout(head)

        body = QLabel(note.get("body") or "")
        body.setWordWrap(True)
        body.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        lay.addWidget(body)
        return frame

    def new_note_dialog(self):
        if not self.selected_patient_id:
            QMessageBox.warning(self, "Error", "Please select a patient first.")
            return
        self._note_dialog(note=None)

    def edit_note_dialog(self, note: dict):
        self._note_dialog(note=note)

    def _note_dialog(self, note: dict | None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Private Note" if note else "New Private Note")
        dialog.setMinimumSize(520, 380)
        lay = QVBoxLayout(dialog)

        hint = QLabel(
            "Only you will see this note. Do not use for information that "
            "must appear in the patient's chart.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #90A4AE; font-size: 11px;")
        lay.addWidget(hint)

        body = QTextEdit()
        body.setPlainText(note.get("body", "") if note else "")
        body.setMinimumHeight(220)
        lay.addWidget(body)

        pin_row = QHBoxLayout()
        pin_btn = QPushButton(
            "📌 Pinned" if (note and note.get("is_pinned")) else "Pin to top")
        pin_btn.setCheckable(True)
        pin_btn.setChecked(bool(note and note.get("is_pinned")))
        pin_row.addWidget(pin_btn)
        pin_row.addStretch()
        lay.addLayout(pin_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel)
        save = QPushButton("Save")
        save.setObjectName("primary_button")
        btn_row.addWidget(save)
        lay.addLayout(btn_row)

        def _save():
            text = body.toPlainText().strip()
            if not text:
                QMessageBox.warning(dialog, "Error", "Note cannot be empty.")
                return
            try:
                if note:
                    self.db_manager.update_provider_note(
                        note["id"],
                        author_id=self.current_user.get("id"),
                        body_plain=text, is_pinned=pin_btn.isChecked())
                else:
                    self.db_manager.create_provider_note(
                        patient_id=self.selected_patient_id,
                        author_id=self.current_user.get("id"),
                        body_plain=text, is_pinned=pin_btn.isChecked())
                dialog.accept()
                self.load_notes(self.selected_patient_id)
            except Exception as e:
                QMessageBox.warning(dialog, "Error", str(e))

        save.clicked.connect(_save)
        dialog.exec()

    def delete_note(self, note: dict):
        reply = QMessageBox.question(
            self, "Delete Note", "Delete this private note? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db_manager.delete_provider_note(
                note["id"], author_id=self.current_user.get("id"))
            self.load_notes(self.selected_patient_id)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def add_patient_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Patient")
        dialog.setMinimumSize(500, 600)
        layout = QVBoxLayout(dialog)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setSpacing(10)

        fields = {}
        for label, key, widget_type in [
            ("First Name*", "first_name", "line"), ("Last Name*", "last_name", "line"),
            ("Date of Birth*", "dob", "date"), ("Gender", "gender", "combo"),
            ("Last 4 SSN", "ssn_last4", "line"), ("Email", "email", "line"),
            ("Phone", "phone", "line"), ("Address", "address", "line"),
            ("City", "city", "line"), ("State", "state", "line"),
            ("Zip Code", "zip_code", "line"),
            ("Emergency Contact", "emergency_contact_name", "line"),
            ("Emergency Phone", "emergency_contact_phone", "line"),
        ]:
            if widget_type == "line":
                w = QLineEdit()
                w.setMinimumHeight(36)
            elif widget_type == "date":
                w = QDateEdit()
                w.setCalendarPopup(True)
                w.setDate(QDate(1990, 1, 1))
                w.setMinimumHeight(36)
            elif widget_type == "combo":
                w = QComboBox()
                w.addItems(["Male", "Female", "Other"])
                w.setMinimumHeight(36)
            form.addRow(label, w)
            fields[key] = w

        scroll.setWidget(form_widget)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("Save Patient")
        save_btn.setObjectName("primary_button")
        save_btn.clicked.connect(lambda: self._save_patient(dialog, fields))
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        dialog.exec()

    def _save_patient(self, dialog, fields):
        from database.models import Gender
        first = fields["first_name"].text().strip()
        last = fields["last_name"].text().strip()
        if not first or not last:
            QMessageBox.warning(dialog, "Error", "First and last name are required.")
            return
        try:
            gender_map = {"Male": Gender.MALE, "Female": Gender.FEMALE, "Other": Gender.OTHER}
            dob = fields["dob"].date().toPyDate()
            self.db_manager.create_patient(
                first_name=first, last_name=last, dob=dob,
                gender=gender_map.get(fields["gender"].currentText()),
                ssn_last4=fields["ssn_last4"].text().strip(),
                email=fields["email"].text().strip(),
                phone=fields["phone"].text().strip(),
                address=fields["address"].text().strip(),
                city=fields["city"].text().strip(),
                state=fields["state"].text().strip(),
                zip_code=fields["zip_code"].text().strip(),
                emergency_contact_name=fields["emergency_contact_name"].text().strip(),
                emergency_contact_phone=fields["emergency_contact_phone"].text().strip()
            )
            dialog.accept()
            self.refresh_data()
            QMessageBox.information(self, "Success", f"Patient {first} {last} created.")
        except Exception as e:
            QMessageBox.warning(dialog, "Error", f"Failed to create patient: {e}")
