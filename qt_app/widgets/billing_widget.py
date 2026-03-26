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
