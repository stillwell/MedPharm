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
MedPharm ERP - Secure Messages Widget (staff side)

Shows the thread list and thread view for clinician-to-patient secure
messaging. Threads are global; filtering by patient is a convenience.
"""

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QSplitter, QTextEdit,
    QScrollArea, QLineEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


class MessagesWidget(QWidget):
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.threads = []
        self.selected_thread_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Secure Messages")
        title.setObjectName("heading")
        header_row.addWidget(title)
        header_row.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setMinimumHeight(38)
        refresh_btn.clicked.connect(self.refresh_data)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter by patient name or subject...")
        self.search.setMinimumHeight(38)
        self.search.textChanged.connect(self.populate_table)
        search_row.addWidget(self.search)
        layout.addLayout(search_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.threads_table = QTableWidget()
        self.threads_table.setColumnCount(5)
        self.threads_table.setHorizontalHeaderLabels(
            ["Patient", "Subject", "Last Activity", "Unread", "Status"])
        self.threads_table.horizontalHeader().setStretchLastSection(True)
        self.threads_table.setAlternatingRowColors(True)
        self.threads_table.verticalHeader().setVisible(False)
        self.threads_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.threads_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.threads_table.currentCellChanged.connect(self.on_thread_selected)
        self.threads_table.setColumnWidth(0, 170)
        self.threads_table.setColumnWidth(1, 220)
        self.threads_table.setColumnWidth(2, 140)
        self.threads_table.setColumnWidth(3, 70)
        splitter.addWidget(self.threads_table)

        detail = QFrame()
        detail.setObjectName("card")
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(16, 16, 16, 16)

        self.thread_title = QLabel("Select a thread to view")
        self.thread_title.setObjectName("section_title")
        detail_layout.addWidget(self.thread_title)

        self.thread_meta = QLabel("")
        self.thread_meta.setStyleSheet("color: #808080; font-size: 12px;")
        detail_layout.addWidget(self.thread_meta)

        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        self.messages_scroll.setWidget(self.messages_container)
        detail_layout.addWidget(self.messages_scroll, 1)

        self.compose = QTextEdit()
        self.compose.setPlaceholderText("Type your reply...")
        self.compose.setMaximumHeight(110)
        detail_layout.addWidget(self.compose)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.close_btn = QPushButton("Close Thread")
        self.close_btn.clicked.connect(self.close_thread)
        self.close_btn.setEnabled(False)
        action_row.addWidget(self.close_btn)
        self.send_btn = QPushButton("Send Reply")
        self.send_btn.setObjectName("primary_button")
        self.send_btn.clicked.connect(self.send_reply)
        self.send_btn.setEnabled(False)
        action_row.addWidget(self.send_btn)
        detail_layout.addLayout(action_row)

        splitter.addWidget(detail)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

    def refresh_data(self):
        try:
            self.threads = self.db_manager.get_message_threads(reader_type="staff")
            self.populate_table()
        except Exception as e:
            print(f"Messages load error: {e}")

    def populate_table(self):
        q = self.search.text().strip().lower()
        rows = self.threads
        if q:
            rows = [t for t in rows
                    if q in (t.get("patient_name") or "").lower()
                    or q in (t.get("subject") or "").lower()]
        self.threads_table.setRowCount(len(rows))
        for i, t in enumerate(rows):
            self.threads_table.setItem(i, 0, QTableWidgetItem(t.get("patient_name") or ""))
            self.threads_table.setItem(i, 1, QTableWidgetItem(t.get("subject") or ""))
            self.threads_table.setItem(i, 2, QTableWidgetItem(
                _fmt_dt(t.get("last_message_at"))))
            unread = t.get("unread_count", 0)
            unread_item = QTableWidgetItem(str(unread) if unread else "")
            if unread:
                unread_item.setForeground(QColor("#E53935"))
                f = QFont()
                f.setBold(True)
                unread_item.setFont(f)
            self.threads_table.setItem(i, 3, unread_item)
            status = "Closed" if t.get("is_closed") else "Open"
            status_item = QTableWidgetItem(status)
            if t.get("is_closed"):
                status_item.setForeground(QColor("#808080"))
            self.threads_table.setItem(i, 4, status_item)
            self.threads_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, t["id"])

    def on_thread_selected(self, row, col, prev_row, prev_col):
        if row < 0:
            return
        item = self.threads_table.item(row, 0)
        if not item:
            return
        thread_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_thread_id = thread_id
        self.load_thread(thread_id)

    def load_thread(self, thread_id):
        try:
            thread = self.db_manager.get_message_thread(thread_id)
            if not thread:
                return
            messages = self.db_manager.get_thread_messages(thread_id)
            self.db_manager.mark_messages_read(thread_id, reader_type="staff")

            self.thread_title.setText(thread.get("subject") or "")
            self.thread_meta.setText(
                f"Patient: {thread.get('patient_name', '-')}  |  "
                f"Provider: {thread.get('provider_name') or 'unassigned'}  |  "
                f"Opened: {_fmt_dt(thread.get('created_at'))}  |  "
                f"{'Closed' if thread.get('is_closed') else 'Open'}")

            while self.messages_layout.count() > 1:
                item = self.messages_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            for m in messages:
                self.messages_layout.insertWidget(
                    self.messages_layout.count() - 1, _bubble(m))

            self.compose.setEnabled(not thread.get("is_closed"))
            self.send_btn.setEnabled(not thread.get("is_closed"))
            self.close_btn.setEnabled(not thread.get("is_closed"))

            for i, t in enumerate(self.threads):
                if t["id"] == thread_id:
                    t["unread_count"] = 0
                    break
            self.populate_table()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load thread: {e}")

    def send_reply(self):
        if not self.selected_thread_id:
            return
        body = self.compose.toPlainText().strip()
        if not body:
            return
        try:
            self.db_manager.post_secure_message(
                thread_id=self.selected_thread_id,
                sender_type="staff",
                sender_id=self.current_user.get("id"),
                body_plain=body)
            self.compose.clear()
            self.load_thread(self.selected_thread_id)
            self.refresh_data()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to send: {e}")

    def close_thread(self):
        if not self.selected_thread_id:
            return
        reply = QMessageBox.question(
            self, "Close Thread",
            "Close this thread? No further replies will be accepted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db_manager.close_message_thread(self.selected_thread_id)
            self.refresh_data()
            self.load_thread(self.selected_thread_id)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to close thread: {e}")


def _bubble(message: dict) -> QFrame:
    frame = QFrame()
    is_staff = message.get("sender_type") == "staff"
    bg = "#1E3A44" if is_staff else "#2A2D35"
    accent = "#00BCD4" if is_staff else "#78909C"
    frame.setStyleSheet(
        f"background-color: {bg}; border-radius: 8px; "
        f"border-left: 3px solid {accent};")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(12, 8, 12, 8)

    header = QLabel(
        f"<b>{'Clinical Staff' if is_staff else 'Patient'}</b>"
        f" &middot; {_fmt_dt(message.get('sent_at'))}"
        f"{' &middot; unread' if not message.get('read_at') else ''}")
    header.setStyleSheet("color: #b0b0b0; font-size: 11px;")
    lay.addWidget(header)

    body = QLabel(message.get("body") or "")
    body.setWordWrap(True)
    body.setStyleSheet("color: #e0e0e0; font-size: 13px;")
    lay.addWidget(body)
    return frame


def _fmt_dt(s) -> str:
    if not s:
        return "-"
    try:
        return datetime.fromisoformat(s).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        return str(s)
