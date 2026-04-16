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
MedPharm ERP - Billing Management Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QDialog, QFormLayout, QDoubleSpinBox, QTextEdit,
    QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from datetime import date, timedelta


class BillingWidget(QWidget):
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.all_invoices = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Billing & Payments")
        title.setObjectName("heading")
        header_row.addWidget(title)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Revenue Summary Cards
        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)
        self.summary_cards = {}
        for key, label, color in [
            ("today", "Today's Revenue", "#43A047"),
            ("outstanding", "Outstanding Balance", "#E53935"),
            ("paid_month", "Monthly Revenue", "#7C4DFF"),
            ("total_invoices", "Total Invoices", "#00BCD4"),
        ]:
            card = self._create_summary_card(label, "$0.00", color)
            self.summary_cards[key] = card
            summary_row.addWidget(card["frame"])
        layout.addLayout(summary_row)

        # Filters
        filter_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by invoice# or patient...")
        self.search_input.setMinimumHeight(38)
        self.search_input.textChanged.connect(self.apply_filter)
        filter_row.addWidget(self.search_input, 3)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Sent", "Partial", "Paid", "Overdue", "Draft", "Cancelled"])
        self.status_filter.setMinimumHeight(38)
        self.status_filter.currentTextChanged.connect(self.refresh_data)
        filter_row.addWidget(self.status_filter, 1)
        layout.addLayout(filter_row)

        # Invoice Table
        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(8)
        self.invoice_table.setHorizontalHeaderLabels([
            "Invoice#", "Patient", "Date", "Due Date", "Total", "Paid", "Balance", "Status"
        ])
        self.invoice_table.horizontalHeader().setStretchLastSection(True)
        self.invoice_table.setAlternatingRowColors(True)
        self.invoice_table.verticalHeader().setVisible(False)
        self.invoice_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoice_table.doubleClicked.connect(self.view_invoice_detail)
        self.invoice_table.setColumnWidth(0, 130)
        self.invoice_table.setColumnWidth(1, 150)
        self.invoice_table.setColumnWidth(2, 100)
        self.invoice_table.setColumnWidth(3, 100)
        layout.addWidget(self.invoice_table)

        # Action buttons
        action_row = QHBoxLayout()
        action_row.addStretch()

        record_pay_btn = QPushButton("Record Payment")
        record_pay_btn.setObjectName("success_button")
        record_pay_btn.setMinimumHeight(40)
        record_pay_btn.clicked.connect(self.record_payment_dialog)
        action_row.addWidget(record_pay_btn)

        claim_btn = QPushButton("Submit Insurance Claim")
        claim_btn.setObjectName("primary_button")
        claim_btn.setMinimumHeight(40)
        claim_btn.clicked.connect(self.submit_claim_dialog)
        action_row.addWidget(claim_btn)

        view_claims_btn = QPushButton("View Claims")
        view_claims_btn.setMinimumHeight(40)
        view_claims_btn.clicked.connect(self.show_claims_dialog)
        action_row.addWidget(view_claims_btn)

        view_btn = QPushButton("View Detail")
        view_btn.setObjectName("primary_button")
        view_btn.setMinimumHeight(40)
        view_btn.clicked.connect(lambda: self.view_invoice_detail(self.invoice_table.currentIndex()))
        action_row.addWidget(view_btn)
        layout.addLayout(action_row)

        # Payment History
        pay_title = QLabel("Recent Payments")
        pay_title.setObjectName("section_title")
        layout.addWidget(pay_title)

        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(6)
        self.payment_table.setHorizontalHeaderLabels(["Invoice#", "Amount", "Method", "Reference", "Date", "Status"])
        self.payment_table.horizontalHeader().setStretchLastSection(True)
        self.payment_table.setAlternatingRowColors(True)
        self.payment_table.verticalHeader().setVisible(False)
        self.payment_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.payment_table.setMaximumHeight(200)
        layout.addWidget(self.payment_table)

    def _create_summary_card(self, label, value, color):
        frame = QFrame()
        frame.setObjectName("kpi_card")
        frame.setStyleSheet(f"QFrame#kpi_card {{ border-top: 3px solid {color}; }}")
        lo = QVBoxLayout(frame)
        lo.setSpacing(4)
        val = QLabel(value)
        val.setObjectName("card_value")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(val)
        lbl = QLabel(label)
        lbl.setObjectName("card_label")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(lbl)
        return {"frame": frame, "value_label": val}

    def refresh_data(self):
        try:
            status_text = self.status_filter.currentText() if hasattr(self, "status_filter") else "All Status"
            status = None if status_text == "All Status" else status_text.lower()
            self.all_invoices = self.db_manager.get_all_invoices(status)
            self.apply_filter()

            # Update summary cards
            stats = self.db_manager.get_dashboard_stats()
            self.summary_cards["today"]["value_label"].setText(f"${stats.get('today_revenue', 0):,.2f}")
            self.summary_cards["outstanding"]["value_label"].setText(f"${stats.get('pending_bills', 0):,.2f}")
            self.summary_cards["paid_month"]["value_label"].setText(f"${stats.get('monthly_revenue', 0):,.2f}")
            self.summary_cards["total_invoices"]["value_label"].setText(str(len(self.all_invoices)))

            # Payment history
            payments = self.db_manager.get_payment_history()
            self.payment_table.setRowCount(min(len(payments), 20))
            for i, p in enumerate(payments[:20]):
                self.payment_table.setItem(i, 0, QTableWidgetItem(p.get("invoice_number", "")))
                self.payment_table.setItem(i, 1, QTableWidgetItem(f"${p.get('amount', 0):.2f}"))
                self.payment_table.setItem(i, 2, QTableWidgetItem(p.get("payment_method", "").replace("_", " ").title()))
                self.payment_table.setItem(i, 3, QTableWidgetItem(p.get("transaction_reference", "")))
                dt = p.get("payment_date", "")
                if dt:
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(dt).strftime("%m/%d/%Y")
                    except (ValueError, TypeError):
                        pass
                self.payment_table.setItem(i, 4, QTableWidgetItem(str(dt)))
                self.payment_table.setItem(i, 5, QTableWidgetItem(p.get("status", "").title()))
        except Exception as e:
            print(f"Billing refresh error: {e}")

    def apply_filter(self):
        search = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        invs = self.all_invoices
        if search:
            invs = [i for i in invs if
                    search in i.get("invoice_number", "").lower() or
                    search in i.get("patient_name", "").lower()]
        self.populate_table(invs)

    def populate_table(self, invoices):
        status_colors = {
            "draft": QColor(128, 128, 128), "sent": QColor(3, 155, 229),
            "partial": QColor(251, 140, 0), "paid": QColor(67, 160, 71),
            "overdue": QColor(229, 57, 53), "cancelled": QColor(128, 128, 128)
        }
        self.invoice_table.setRowCount(len(invoices))
        for i, inv in enumerate(invoices):
            self.invoice_table.setItem(i, 0, QTableWidgetItem(inv.get("invoice_number", "")))
            self.invoice_table.setItem(i, 1, QTableWidgetItem(inv.get("patient_name", "")))
            self.invoice_table.setItem(i, 2, QTableWidgetItem(inv.get("invoice_date", "")))
            self.invoice_table.setItem(i, 3, QTableWidgetItem(inv.get("due_date", "")))
            self.invoice_table.setItem(i, 4, QTableWidgetItem(f"${inv.get('total_amount', 0):.2f}"))
            self.invoice_table.setItem(i, 5, QTableWidgetItem(f"${inv.get('amount_paid', 0):.2f}"))
            self.invoice_table.setItem(i, 6, QTableWidgetItem(f"${inv.get('balance_due', 0):.2f}"))

            status = inv.get("status", "")
            status_item = QTableWidgetItem(status.title())
            color = status_colors.get(status, QColor(128, 128, 128))
            status_item.setForeground(color)
            self.invoice_table.setItem(i, 7, status_item)

            # Highlight overdue rows
            if status == "overdue":
                for col in range(8):
                    item = self.invoice_table.item(i, col)
                    if item:
                        item.setBackground(QColor(229, 57, 53, 30))

    def view_invoice_detail(self, index):
        row = index.row() if hasattr(index, 'row') else self.invoice_table.currentRow()
        if row < 0:
            return
        inv_num_item = self.invoice_table.item(row, 0)
        if not inv_num_item:
            return
        inv = next((i for i in self.all_invoices if i["invoice_number"] == inv_num_item.text()), None)
        if not inv:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Invoice {inv['invoice_number']}")
        dialog.setMinimumSize(550, 500)
        layout = QVBoxLayout(dialog)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        clayout = QVBoxLayout(content)

        # Header
        info = QGroupBox("Invoice Information")
        info_layout = QFormLayout(info)
        info_layout.addRow("Invoice #:", QLabel(inv["invoice_number"]))
        info_layout.addRow("Patient:", QLabel(inv["patient_name"]))
        info_layout.addRow("Date:", QLabel(inv.get("invoice_date", "")))
        info_layout.addRow("Due Date:", QLabel(inv.get("due_date", "")))
        info_layout.addRow("Status:", QLabel(inv["status"].title()))
        clayout.addWidget(info)

        # Line items
        items_group = QGroupBox("Line Items")
        items_layout = QVBoxLayout(items_group)
        items_table = QTableWidget()
        items_table.setColumnCount(4)
        items_table.setHorizontalHeaderLabels(["Description", "Code", "Qty", "Amount"])
        items_table.horizontalHeader().setStretchLastSection(True)
        items_table.verticalHeader().setVisible(False)
        items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        items_data = inv.get("items", [])
        items_table.setRowCount(len(items_data))
        for i, item in enumerate(items_data):
            items_table.setItem(i, 0, QTableWidgetItem(item.get("description", "")))
            items_table.setItem(i, 1, QTableWidgetItem(item.get("service_code", "")))
            items_table.setItem(i, 2, QTableWidgetItem(str(item.get("quantity", 1))))
            items_table.setItem(i, 3, QTableWidgetItem(f"${item.get('total_price', 0):.2f}"))
        items_layout.addWidget(items_table)
        clayout.addWidget(items_group)

        # Totals
        totals_frame = QFrame()
        totals_frame.setObjectName("card")
        tl = QVBoxLayout(totals_frame)
        for label, val in [("Subtotal", inv.get("subtotal", 0)),
                           ("Tax", inv.get("tax", 0)),
                           ("Total", inv.get("total_amount", 0)),
                           ("Paid", inv.get("amount_paid", 0)),
                           ("Balance Due", inv.get("balance_due", 0))]:
            row = QHBoxLayout()
            l = QLabel(f"{label}:")
            l.setStyleSheet("font-weight: 500;")
            row.addWidget(l)
            row.addStretch()
            v = QLabel(f"${val:.2f}")
            v.setStyleSheet("font-weight: 700; font-size: 14px;")
            if label == "Balance Due" and val > 0:
                v.setStyleSheet("font-weight: 700; font-size: 14px; color: #E53935;")
            elif label == "Balance Due":
                v.setStyleSheet("font-weight: 700; font-size: 14px; color: #43A047;")
            row.addWidget(v)
            tl.addLayout(row)
        clayout.addWidget(totals_frame)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
        dialog.exec()

    def record_payment_dialog(self):
        row = self.invoice_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select an invoice.")
            return
        inv_num_item = self.invoice_table.item(row, 0)
        if not inv_num_item:
            return
        inv = next((i for i in self.all_invoices if i["invoice_number"] == inv_num_item.text()), None)
        if not inv:
            return
        if inv["status"] in ("paid", "cancelled"):
            QMessageBox.warning(self, "Error", "This invoice is already paid or cancelled.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Record Payment - {inv['invoice_number']}")
        dialog.setMinimumSize(400, 350)
        layout = QVBoxLayout(dialog)

        info = QLabel(f"Invoice: {inv['invoice_number']}\nPatient: {inv['patient_name']}\n"
                      f"Balance Due: ${inv['balance_due']:.2f}")
        info.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)

        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0.01, inv["balance_due"])
        amount_spin.setValue(inv["balance_due"])
        amount_spin.setPrefix("$ ")
        amount_spin.setDecimals(2)
        amount_spin.setMinimumHeight(36)
        form.addRow("Amount:", amount_spin)

        method_combo = QComboBox()
        method_combo.addItems(["credit_card", "debit_card", "cash", "check", "insurance", "online"])
        method_combo.setMinimumHeight(36)
        form.addRow("Method:", method_combo)

        notes_edit = QLineEdit()
        notes_edit.setPlaceholderText("Payment notes...")
        notes_edit.setMinimumHeight(36)
        form.addRow("Notes:", notes_edit)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        pay_btn = QPushButton("Record Payment")
        pay_btn.setObjectName("success_button")
        pay_btn.clicked.connect(lambda: self._process_payment(
            dialog, inv["id"], amount_spin.value(), method_combo.currentText(), notes_edit.text()))
        btn_row.addWidget(pay_btn)
        layout.addLayout(btn_row)

        dialog.exec()

    def _process_payment(self, dialog, invoice_id, amount, method, notes):
        try:
            self.db_manager.record_payment(
                invoice_id=invoice_id, amount=amount,
                payment_method=method, notes=notes
            )
            dialog.accept()
            self.refresh_data()
            QMessageBox.information(self, "Success", f"Payment of ${amount:.2f} recorded.")
        except Exception as e:
            QMessageBox.warning(dialog, "Error", str(e))

    def submit_claim_dialog(self):
        """Submit an insurance claim for the selected invoice."""
        row = self.invoice_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select an invoice.")
            return
        inv_num_item = self.invoice_table.item(row, 0)
        if not inv_num_item:
            return
        inv = next((i for i in self.all_invoices if i["invoice_number"] == inv_num_item.text()), None)
        if not inv:
            return
        if inv["status"] in ("paid", "cancelled"):
            QMessageBox.warning(self, "Error", "Cannot submit claim for paid/cancelled invoice.")
            return

        insurances = self.db_manager.get_patient_insurance(inv["patient_id"])
        active = [i for i in insurances if i.get("is_active", True)]
        if not active:
            QMessageBox.warning(self, "No Insurance",
                "This patient has no active insurance on file.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Insurance Claim - {inv['invoice_number']}")
        dialog.setMinimumSize(460, 400)
        layout = QVBoxLayout(dialog)

        info = QLabel(
            f"Invoice: {inv['invoice_number']}\n"
            f"Patient: {inv['patient_name']}\n"
            f"Balance Due: ${inv['balance_due']:.2f}"
        )
        info.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)

        ins_combo = QComboBox()
        for ins in active:
            label = f"{ins['provider_name']} ({ins['policy_number']})"
            ins_combo.addItem(label, ins["id"])
        ins_combo.setMinimumHeight(36)
        form.addRow("Insurance:", ins_combo)

        claim_amount = QDoubleSpinBox()
        claim_amount.setRange(0.01, inv["balance_due"])
        claim_amount.setValue(inv["balance_due"])
        claim_amount.setPrefix("$ ")
        claim_amount.setDecimals(2)
        claim_amount.setMinimumHeight(36)
        form.addRow("Claimed Amount:", claim_amount)

        copay_amount = QDoubleSpinBox()
        copay_amount.setRange(0, inv["balance_due"])
        default_copay = next((i.get("copay_amount") or 0 for i in active), 0)
        copay_amount.setValue(float(default_copay or 0))
        copay_amount.setPrefix("$ ")
        copay_amount.setDecimals(2)
        copay_amount.setMinimumHeight(36)
        form.addRow("Copay:", copay_amount)

        notes_edit = QTextEdit()
        notes_edit.setPlaceholderText("Claim notes (diagnosis codes, procedure codes, etc.)")
        notes_edit.setMaximumHeight(80)
        form.addRow("Notes:", notes_edit)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        submit_btn = QPushButton("Submit Claim")
        submit_btn.setObjectName("primary_button")
        submit_btn.clicked.connect(lambda: self._process_claim_submit(
            dialog, inv, ins_combo.currentData(),
            claim_amount.value(), copay_amount.value(),
            notes_edit.toPlainText()
        ))
        btn_row.addWidget(submit_btn)
        layout.addLayout(btn_row)

        dialog.exec()

    def _process_claim_submit(self, dialog, inv, insurance_id, claimed, copay, notes):
        try:
            claim_id = self.db_manager.submit_insurance_claim(
                invoice_id=inv["id"],
                insurance_id=insurance_id,
                patient_id=inv["patient_id"],
                claimed_amount=claimed,
                copay_amount=copay,
                notes=notes
            )
            dialog.accept()
            self.refresh_data()
            QMessageBox.information(self, "Success",
                f"Insurance claim submitted successfully.\nClaim ID: {claim_id}")
        except Exception as e:
            QMessageBox.warning(dialog, "Error", str(e))

    def show_claims_dialog(self):
        """Display all insurance claims with option to process approvals."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Insurance Claims Management")
        dialog.setMinimumSize(900, 550)
        layout = QVBoxLayout(dialog)

        title = QLabel("Insurance Claims")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px;")
        layout.addWidget(title)

        claims_table = QTableWidget()
        claims_table.setColumnCount(8)
        claims_table.setHorizontalHeaderLabels([
            "Claim #", "Invoice", "Provider", "Claimed",
            "Approved", "Copay", "Status", "Submitted"
        ])
        claims_table.horizontalHeader().setStretchLastSection(True)
        claims_table.setAlternatingRowColors(True)
        claims_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        claims_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        def load_claims():
            claims = self.db_manager.get_insurance_claims()
            claims_table.setRowCount(len(claims))
            for row, c in enumerate(claims):
                claims_table.setItem(row, 0, QTableWidgetItem(c["claim_number"]))
                claims_table.setItem(row, 1, QTableWidgetItem(str(c["invoice_id"])))
                claims_table.setItem(row, 2, QTableWidgetItem(c["insurance_provider"]))
                claims_table.setItem(row, 3, QTableWidgetItem(f"${c['claimed_amount']:.2f}"))
                claims_table.setItem(row, 4, QTableWidgetItem(f"${c['approved_amount']:.2f}"))
                claims_table.setItem(row, 5, QTableWidgetItem(f"${c['copay_amount']:.2f}"))
                status_item = QTableWidgetItem(c["status"].replace("_", " ").title())
                status_colors = {
                    "submitted": QColor("#FFA726"),
                    "in_review": QColor("#42A5F5"),
                    "approved": QColor("#66BB6A"),
                    "partially_approved": QColor("#9CCC65"),
                    "denied": QColor("#EF5350"),
                    "paid": QColor("#26A69A"),
                }
                color = status_colors.get(c["status"], QColor("#BDBDBD"))
                status_item.setForeground(color)
                claims_table.setItem(row, 6, status_item)
                claims_table.setItem(row, 7, QTableWidgetItem(c.get("submitted_date", "") or ""))
                claims_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, c)

        load_claims()
        layout.addWidget(claims_table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        process_btn = QPushButton("Process Payment")
        process_btn.setObjectName("success_button")
        process_btn.setMinimumHeight(40)

        def do_process():
            row = claims_table.currentRow()
            if row < 0:
                QMessageBox.warning(dialog, "Error", "Select a claim to process.")
                return
            claim_data = claims_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if claim_data["status"] not in ("submitted", "in_review"):
                QMessageBox.warning(dialog, "Error",
                    "Only submitted/in-review claims can be processed.")
                return
            self._process_claim_payment_dialog(dialog, claim_data, load_claims)

        process_btn.clicked.connect(do_process)
        btn_row.addWidget(process_btn)

        deny_btn = QPushButton("Deny Claim")
        deny_btn.setObjectName("danger_button")
        deny_btn.setMinimumHeight(40)

        def do_deny():
            row = claims_table.currentRow()
            if row < 0:
                return
            claim_data = claims_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            reason, ok = self._prompt_text(dialog, "Denial Reason",
                "Enter reason for denial:")
            if ok and reason:
                self.db_manager.update_insurance_claim(
                    claim_data["id"], status="denied", denial_reason=reason)
                load_claims()

        deny_btn.clicked.connect(do_deny)
        btn_row.addWidget(deny_btn)

        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)
        dialog.exec()

    def _process_claim_payment_dialog(self, parent_dialog, claim, reload_callback):
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle(f"Process Claim - {claim['claim_number']}")
        dialog.setMinimumSize(420, 340)
        layout = QVBoxLayout(dialog)

        info = QLabel(
            f"Claim: {claim['claim_number']}\n"
            f"Provider: {claim['insurance_provider']}\n"
            f"Claimed: ${claim['claimed_amount']:.2f}"
        )
        info.setStyleSheet("font-size: 13px; padding: 8px;")
        layout.addWidget(info)

        form = QFormLayout()
        approved_spin = QDoubleSpinBox()
        approved_spin.setRange(0, claim["claimed_amount"])
        approved_spin.setValue(claim["claimed_amount"])
        approved_spin.setPrefix("$ ")
        approved_spin.setDecimals(2)
        approved_spin.setMinimumHeight(36)
        form.addRow("Approved Amount:", approved_spin)

        copay_spin = QDoubleSpinBox()
        copay_spin.setRange(0, claim["claimed_amount"])
        copay_spin.setValue(float(claim.get("copay_amount") or 0))
        copay_spin.setPrefix("$ ")
        copay_spin.setDecimals(2)
        copay_spin.setMinimumHeight(36)
        form.addRow("Patient Copay:", copay_spin)

        deductible_spin = QDoubleSpinBox()
        deductible_spin.setRange(0, claim["claimed_amount"])
        deductible_spin.setPrefix("$ ")
        deductible_spin.setDecimals(2)
        deductible_spin.setMinimumHeight(36)
        form.addRow("Deductible:", deductible_spin)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        approve_btn = QPushButton("Approve & Record Payment")
        approve_btn.setObjectName("success_button")

        def do_approve():
            try:
                result = self.db_manager.process_insurance_payment(
                    claim_id=claim["id"],
                    approved_amount=approved_spin.value(),
                    copay_amount=copay_spin.value(),
                    deductible=deductible_spin.value()
                )
                if result.get("error"):
                    QMessageBox.warning(dialog, "Error", result["error"])
                    return
                dialog.accept()
                reload_callback()
                self.refresh_data()
                QMessageBox.information(parent_dialog, "Success",
                    f"Claim approved.\nInsurance paid: ${result['insurance_paid']:.2f}\n"
                    f"Remaining balance: ${result['remaining_balance']:.2f}")
            except Exception as e:
                QMessageBox.warning(dialog, "Error", str(e))

        approve_btn.clicked.connect(do_approve)
        btn_row.addWidget(approve_btn)
        layout.addLayout(btn_row)

        dialog.exec()

    def _prompt_text(self, parent, title, label):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(parent, title, label)
        return text, ok
