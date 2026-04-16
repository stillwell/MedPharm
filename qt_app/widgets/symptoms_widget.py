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
MedPharm ERP - Symptoms & Conditions Reference Widget
Browse and search the medical reference database of symptoms and conditions.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QSplitter, QTabWidget,
    QPushButton, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


class SymptomsWidget(QWidget):
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        title = QLabel("Symptoms & Conditions Reference")
        title.setObjectName("heading")
        layout.addWidget(title)

        subtitle = QLabel(
            "Browse the medical reference database of symptoms and conditions "
            "to help with diagnosis and treatment."
        )
        subtitle.setStyleSheet("color: #9ca0a8; font-size: 12px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Tab widget for Symptoms / Conditions
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_symptoms_tab(), "Symptoms")
        self.tabs.addTab(self._build_conditions_tab(), "Conditions")
        layout.addWidget(self.tabs)

    # ── Symptoms Tab ─────────────────────────────────────────────────────

    def _build_symptoms_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Filters
        filter_row = QHBoxLayout()
        self.symptom_search = QLineEdit()
        self.symptom_search.setPlaceholderText("Search symptoms by name or description...")
        self.symptom_search.setMinimumHeight(38)
        self.symptom_search.textChanged.connect(self.refresh_symptoms)
        filter_row.addWidget(self.symptom_search, 3)

        self.body_system_filter = QComboBox()
        self.body_system_filter.setMinimumHeight(38)
        self.body_system_filter.currentTextChanged.connect(self.refresh_symptoms)
        filter_row.addWidget(self.body_system_filter, 1)
        layout.addLayout(filter_row)

        # Splitter: list + detail
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.symptoms_table = QTableWidget()
        self.symptoms_table.setColumnCount(3)
        self.symptoms_table.setHorizontalHeaderLabels(["Name", "Body System", "Emergency"])
        self.symptoms_table.horizontalHeader().setStretchLastSection(True)
        self.symptoms_table.setAlternatingRowColors(True)
        self.symptoms_table.verticalHeader().setVisible(False)
        self.symptoms_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.symptoms_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.symptoms_table.currentCellChanged.connect(self.on_symptom_selected)
        splitter.addWidget(self.symptoms_table)

        self.symptom_detail = QTextEdit()
        self.symptom_detail.setReadOnly(True)
        splitter.addWidget(self.symptom_detail)

        splitter.setSizes([450, 450])
        layout.addWidget(splitter)

        return widget

    def _build_conditions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Filters
        filter_row = QHBoxLayout()
        self.condition_search = QLineEdit()
        self.condition_search.setPlaceholderText("Search conditions by name, ICD-10 code, or description...")
        self.condition_search.setMinimumHeight(38)
        self.condition_search.textChanged.connect(self.refresh_conditions)
        filter_row.addWidget(self.condition_search, 3)

        self.category_filter = QComboBox()
        self.category_filter.setMinimumHeight(38)
        self.category_filter.currentTextChanged.connect(self.refresh_conditions)
        filter_row.addWidget(self.category_filter, 1)
        layout.addLayout(filter_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.conditions_table = QTableWidget()
        self.conditions_table.setColumnCount(4)
        self.conditions_table.setHorizontalHeaderLabels(["Name", "ICD-10", "Category", "Chronic"])
        self.conditions_table.horizontalHeader().setStretchLastSection(True)
        self.conditions_table.setAlternatingRowColors(True)
        self.conditions_table.verticalHeader().setVisible(False)
        self.conditions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.conditions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.conditions_table.currentCellChanged.connect(self.on_condition_selected)
        splitter.addWidget(self.conditions_table)

        self.condition_detail = QTextEdit()
        self.condition_detail.setReadOnly(True)
        splitter.addWidget(self.condition_detail)

        splitter.setSizes([500, 500])
        layout.addWidget(splitter)

        return widget

    def refresh_data(self):
        # Load filter options
        try:
            body_systems = self.db_manager.get_all_body_systems()
            self.body_system_filter.clear()
            self.body_system_filter.addItem("All Systems", "")
            for s in body_systems:
                self.body_system_filter.addItem(s, s)

            categories = self.db_manager.get_all_condition_categories()
            self.category_filter.clear()
            self.category_filter.addItem("All Categories", "")
            for c in categories:
                self.category_filter.addItem(c, c)
        except Exception:
            pass

        self.refresh_symptoms()
        self.refresh_conditions()

    def refresh_symptoms(self):
        try:
            query = self.symptom_search.text().strip()
            body_system = self.body_system_filter.currentData() or ""
            symptoms = self.db_manager.search_symptoms(query=query, body_system=body_system)
            self._symptoms_data = symptoms
            self.symptoms_table.setRowCount(len(symptoms))
            for row, s in enumerate(symptoms):
                name_item = QTableWidgetItem(s["name"])
                self.symptoms_table.setItem(row, 0, name_item)
                self.symptoms_table.setItem(row, 1, QTableWidgetItem(s.get("body_system", "") or ""))
                emergency_text = "⚠ YES" if s.get("is_emergency") else "No"
                em_item = QTableWidgetItem(emergency_text)
                if s.get("is_emergency"):
                    em_item.setForeground(QColor("#E53935"))
                    font = QFont()
                    font.setBold(True)
                    em_item.setFont(font)
                self.symptoms_table.setItem(row, 2, em_item)
        except Exception as e:
            self.symptom_detail.setText(f"Error loading symptoms: {e}")

    def refresh_conditions(self):
        try:
            query = self.condition_search.text().strip()
            category = self.category_filter.currentData() or ""
            conditions = self.db_manager.search_conditions(query=query, category=category)
            self._conditions_data = conditions
            self.conditions_table.setRowCount(len(conditions))
            for row, c in enumerate(conditions):
                self.conditions_table.setItem(row, 0, QTableWidgetItem(c["name"]))
                self.conditions_table.setItem(row, 1, QTableWidgetItem(c.get("icd10_code", "") or ""))
                self.conditions_table.setItem(row, 2, QTableWidgetItem(c.get("category", "") or ""))
                chronic_text = "Yes" if c.get("is_chronic") else "No"
                self.conditions_table.setItem(row, 3, QTableWidgetItem(chronic_text))
        except Exception as e:
            self.condition_detail.setText(f"Error loading conditions: {e}")

    def on_symptom_selected(self, row, _col, _prev_row, _prev_col):
        if row < 0 or not hasattr(self, "_symptoms_data"):
            return
        if row >= len(self._symptoms_data):
            return
        s = self._symptoms_data[row]
        html = f"""
        <h2 style='color: #00BCD4;'>{s['name']}</h2>
        <p><b>Body System:</b> {s.get('body_system') or '—'}</p>
        {"<p style='color: #E53935;'><b>⚠ Emergency:</b> This symptom may require immediate medical attention.</p>" if s.get('is_emergency') else ""}
        <h3>Description</h3>
        <p>{s.get('description') or 'No description available.'}</p>
        <h3>Common Associated Conditions</h3>
        <p>{s.get('common_conditions') or 'None listed.'}</p>
        <h3>ICD-10 Codes</h3>
        <p>{s.get('icd10_codes') or 'Not specified.'}</p>
        """
        self.symptom_detail.setHtml(html)

    def on_condition_selected(self, row, _col, _prev_row, _prev_col):
        if row < 0 or not hasattr(self, "_conditions_data"):
            return
        if row >= len(self._conditions_data):
            return
        c = self._conditions_data[row]
        html = f"""
        <h2 style='color: #00BCD4;'>{c['name']}</h2>
        <p><b>ICD-10:</b> {c.get('icd10_code') or '—'} &nbsp;&nbsp;
           <b>Category:</b> {c.get('category') or '—'}</p>
        <p><b>Chronic:</b> {'Yes' if c.get('is_chronic') else 'No'} &nbsp;&nbsp;
           <b>Prevalence:</b> {c.get('prevalence') or 'Not specified'}</p>
        <h3>Description</h3>
        <p>{c.get('description') or 'No description available.'}</p>
        <h3>Common Symptoms</h3>
        <p>{c.get('common_symptoms') or 'None listed.'}</p>
        <h3>Typical Medications</h3>
        <p>{c.get('typical_medications') or 'None listed.'}</p>
        """
        self.condition_detail.setHtml(html)
