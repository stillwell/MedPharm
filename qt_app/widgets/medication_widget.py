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
MedPharm ERP - Medication Database Widget
"""

import csv
import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QSplitter, QTextEdit, QGroupBox, QScrollArea,
    QFileDialog, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


class MedicationWidget(QWidget):
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.all_meds = []
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left: List ──
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 8, 16)
        left_layout.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel("Medication Database")
        title.setObjectName("heading")
        header_row.addWidget(title)
        header_row.addStretch()

        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self.export_csv)
        header_row.addWidget(export_btn)

        refresh_btn = QPushButton("Simulate Price Update")
        refresh_btn.setObjectName("warning_button")
        refresh_btn.clicked.connect(self.simulate_price_update)
        header_row.addWidget(refresh_btn)
        left_layout.addLayout(header_row)

        # Stats
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #808080; font-size: 12px;")
        left_layout.addWidget(self.stats_label)

        # Filters
        filter_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or NDC...")
        self.search_input.setMinimumHeight(38)
        self.search_input.textChanged.connect(self.apply_filter)
        filter_row.addWidget(self.search_input, 3)

        self.class_filter = QComboBox()
        self.class_filter.addItem("All Classes")
        self.class_filter.setMinimumHeight(38)
        self.class_filter.currentTextChanged.connect(self.apply_filter)
        filter_row.addWidget(self.class_filter, 1)

        self.schedule_filter = QComboBox()
        self.schedule_filter.addItems(["All Schedules", "Non-Controlled", "Schedule II", "Schedule III", "Schedule IV", "Schedule V"])
        self.schedule_filter.setMinimumHeight(38)
        self.schedule_filter.currentTextChanged.connect(self.apply_filter)
        filter_row.addWidget(self.schedule_filter, 1)
        left_layout.addLayout(filter_row)

        self.med_table = QTableWidget()
        self.med_table.setColumnCount(8)
        self.med_table.setHorizontalHeaderLabels(["NDC", "Brand Name", "Generic Name", "Class", "Schedule", "Form", "Strength", "Price"])
        self.med_table.horizontalHeader().setStretchLastSection(True)
        self.med_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.med_table.setAlternatingRowColors(True)
        self.med_table.verticalHeader().setVisible(False)
        self.med_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.med_table.currentCellChanged.connect(self.on_med_selected)
        self.med_table.setColumnWidth(0, 120)
        self.med_table.setColumnWidth(1, 140)
        self.med_table.setColumnWidth(2, 140)
        self.med_table.setColumnWidth(3, 120)
        left_layout.addWidget(self.med_table)
        splitter.addWidget(left)

        # ── Right: Detail ──
        right = QScrollArea()
        right.setWidgetResizable(True)
        right.setFrameShape(QFrame.Shape.NoFrame)
        right.setMaximumWidth(450)
        detail = QWidget()
        self.detail_layout = QVBoxLayout(detail)
        self.detail_layout.setContentsMargins(8, 16, 16, 16)
        self.detail_layout.setSpacing(12)

        self.med_title = QLabel("Select a medication")
        self.med_title.setObjectName("heading")
        self.med_title.setWordWrap(True)
        self.detail_layout.addWidget(self.med_title)

        self.med_generic = QLabel("")
        self.med_generic.setObjectName("subheading")
        self.detail_layout.addWidget(self.med_generic)

        # Info cards
        self.info_group = QGroupBox("Information")
        self.info_layout = QFormLayout = QVBoxLayout(self.info_group)
        self.info_labels = {}
        for key in ["Manufacturer", "Drug Class", "DEA Schedule", "Route", "Form", "Strength", "NDC Code"]:
            row = QHBoxLayout()
            k = QLabel(f"{key}:")
            k.setStyleSheet("color: #808080; font-size: 12px; min-width: 100px;")
            v = QLabel("-")
            v.setStyleSheet("font-weight: 500;")
            v.setWordWrap(True)
            row.addWidget(k)
            row.addWidget(v, 1)
            self.info_layout.addLayout(row)
            self.info_labels[key] = v
        self.detail_layout.addWidget(self.info_group)

        # Price
        self.price_group = QGroupBox("Pricing")
        price_layout = QVBoxLayout(self.price_group)
        self.price_labels = {}
        for key in ["Average Wholesale Price", "Retail Price", "Last Updated"]:
            row = QHBoxLayout()
            k = QLabel(f"{key}:")
            k.setStyleSheet("color: #808080; font-size: 12px;")
            v = QLabel("-")
            v.setStyleSheet("font-weight: 600; font-size: 14px;")
            row.addWidget(k)
            row.addWidget(v, 1)
            price_layout.addLayout(row)
            self.price_labels[key] = v
        self.detail_layout.addWidget(self.price_group)

        # Indications
        self.indications_group = QGroupBox("Indications / Uses")
        ind_layout = QVBoxLayout(self.indications_group)
        self.indications_text = QLabel("-")
        self.indications_text.setWordWrap(True)
        ind_layout.addWidget(self.indications_text)
        self.detail_layout.addWidget(self.indications_group)

        # Contraindications
        self.contra_group = QGroupBox("Contraindications")
        contra_layout = QVBoxLayout(self.contra_group)
        self.contra_text = QLabel("-")
        self.contra_text.setWordWrap(True)
        contra_layout.addWidget(self.contra_text)
        self.detail_layout.addWidget(self.contra_group)

        # Side Effects
        self.side_group = QGroupBox("Side Effects")
        side_layout = QVBoxLayout(self.side_group)
        self.side_text = QLabel("-")
        self.side_text.setWordWrap(True)
        side_layout.addWidget(self.side_text)
        self.detail_layout.addWidget(self.side_group)

        # Interactions
        self.inter_group = QGroupBox("Known Drug Interactions")
        self.inter_layout = QVBoxLayout(self.inter_group)
        self.inter_list = QLabel("Select a medication to view interactions")
        self.inter_list.setWordWrap(True)
        self.inter_layout.addWidget(self.inter_list)
        self.detail_layout.addWidget(self.inter_group)

        self.detail_layout.addStretch()

        right.setWidget(detail)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

    def refresh_data(self):
        try:
            self.all_meds = self.db_manager.get_all_medications()
            # Populate class filter
            classes = sorted(set(m.get("drug_class", "") for m in self.all_meds if m.get("drug_class")))
            current = self.class_filter.currentText()
            self.class_filter.blockSignals(True)
            self.class_filter.clear()
            self.class_filter.addItem("All Classes")
            self.class_filter.addItems(classes)
            if current in classes:
                self.class_filter.setCurrentText(current)
            self.class_filter.blockSignals(False)

            self.apply_filter()

            total = len(self.all_meds)
            controlled = sum(1 for m in self.all_meds if m.get("is_controlled"))
            avg_price = sum(m.get("retail_price", 0) for m in self.all_meds) / max(total, 1)
            self.stats_label.setText(f"Total: {total} medications  |  Controlled: {controlled}  |  Avg Price: ${avg_price:.2f}")
        except Exception as e:
            print(f"Medication refresh error: {e}")

    def apply_filter(self):
        search = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        drug_class = self.class_filter.currentText() if hasattr(self, "class_filter") else "All Classes"
        schedule = self.schedule_filter.currentText() if hasattr(self, "schedule_filter") else "All Schedules"

        meds = self.all_meds
        if search:
            meds = [m for m in meds if search in m.get("brand_name", "").lower()
                    or search in m.get("generic_name", "").lower()
                    or search in m.get("ndc_code", "").lower()]
        if drug_class != "All Classes":
            meds = [m for m in meds if m.get("drug_class") == drug_class]

        schedule_map = {"Schedule II": "II", "Schedule III": "III", "Schedule IV": "IV", "Schedule V": "V"}
        if schedule == "Non-Controlled":
            meds = [m for m in meds if not m.get("is_controlled")]
        elif schedule in schedule_map:
            meds = [m for m in meds if m.get("schedule") == schedule_map[schedule]]

        self.populate_table(meds)

    def populate_table(self, meds):
        self.med_table.setRowCount(len(meds))
        for i, m in enumerate(meds):
            self.med_table.setItem(i, 0, QTableWidgetItem(m.get("ndc_code", "")))

            name_item = QTableWidgetItem(m.get("brand_name", ""))
            if m.get("is_controlled"):
                name_item.setForeground(QColor(255, 87, 34))
            self.med_table.setItem(i, 1, name_item)

            self.med_table.setItem(i, 2, QTableWidgetItem(m.get("generic_name", "")))
            self.med_table.setItem(i, 3, QTableWidgetItem(m.get("drug_class", "")))

            sch = m.get("schedule", "none")
            sch_item = QTableWidgetItem(sch if sch != "none" else "-")
            if sch != "none":
                sch_item.setForeground(QColor(255, 87, 34))
            self.med_table.setItem(i, 4, sch_item)

            self.med_table.setItem(i, 5, QTableWidgetItem((m.get("form") or "").title()))
            self.med_table.setItem(i, 6, QTableWidgetItem(m.get("strength", "")))
            self.med_table.setItem(i, 7, QTableWidgetItem(f"${m.get('retail_price', 0):.2f}"))

    def on_med_selected(self, row, col, prev_row, prev_col):
        if row < 0:
            return
        ndc_item = self.med_table.item(row, 0)
        if not ndc_item:
            return
        ndc = ndc_item.text()
        med = next((m for m in self.all_meds if m.get("ndc_code") == ndc), None)
        if not med:
            return
        self.show_detail(med)

    def show_detail(self, med):
        self.med_title.setText(med.get("brand_name", ""))
        self.med_generic.setText(med.get("generic_name", ""))

        self.info_labels["Manufacturer"].setText(med.get("manufacturer", "-"))
        self.info_labels["Drug Class"].setText(med.get("drug_class", "-"))
        sch = med.get("schedule", "none")
        self.info_labels["DEA Schedule"].setText(f"Schedule {sch}" if sch != "none" else "Non-Controlled")
        self.info_labels["Route"].setText((med.get("route") or "-").title())
        self.info_labels["Form"].setText((med.get("form") or "-").title())
        self.info_labels["Strength"].setText(med.get("strength", "-"))
        self.info_labels["NDC Code"].setText(med.get("ndc_code", "-"))

        self.price_labels["Average Wholesale Price"].setText(f"${med.get('avg_wholesale_price', 0):.2f}")
        self.price_labels["Retail Price"].setText(f"${med.get('retail_price', 0):.2f}")
        self.price_labels["Last Updated"].setText(med.get("last_price_update", "-") or "-")

        self.indications_text.setText(med.get("indications") or "No information available")
        self.contra_text.setText(med.get("contraindications") or "No information available")
        self.side_text.setText(med.get("side_effects") or "No information available")

        # Interactions
        interactions = self.db_manager.get_medication_interactions(med["id"])
        if interactions:
            sev_colors = {"minor": "#FB8C00", "moderate": "#FF9800", "major": "#E53935", "contraindicated": "#B71C1C"}
            lines = []
            for inter in interactions:
                color = sev_colors.get(inter["severity"], "#808080")
                lines.append(f'<span style="color:{color};font-weight:bold;">[{inter["severity"].upper()}]</span> '
                             f'{inter["other_medication"]}: {inter["description"]}')
            self.inter_list.setText("<br><br>".join(lines))
        else:
            self.inter_list.setText("No known interactions in database.")

    def simulate_price_update(self):
        reply = QMessageBox.question(self, "Price Update",
            "Simulate a market price update (random +/-5% change)?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            for med in self.all_meds:
                factor = 1 + random.uniform(-0.05, 0.05)
                new_awp = round(med["avg_wholesale_price"] * factor, 2)
                new_retail = round(med["retail_price"] * factor, 2)
                self.db_manager.update_medication_prices(med["id"], new_awp, new_retail)
            self.refresh_data()
            QMessageBox.information(self, "Success", "Medication prices updated.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Medications", "medications.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["NDC", "Brand Name", "Generic Name", "Manufacturer", "Class",
                                 "Schedule", "Route", "Form", "Strength", "AWP", "Retail Price",
                                 "Indications", "Contraindications", "Side Effects"])
                for m in self.all_meds:
                    writer.writerow([
                        m.get("ndc_code"), m.get("brand_name"), m.get("generic_name"),
                        m.get("manufacturer"), m.get("drug_class"), m.get("schedule"),
                        m.get("route"), m.get("form"), m.get("strength"),
                        m.get("avg_wholesale_price"), m.get("retail_price"),
                        m.get("indications"), m.get("contraindications"), m.get("side_effects")
                    ])
            QMessageBox.information(self, "Success", f"Exported {len(self.all_meds)} medications to {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
