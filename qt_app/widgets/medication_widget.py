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
from urllib.parse import quote_plus
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QSplitter, QTextEdit, QGroupBox, QScrollArea,
    QFileDialog, QHeaderView
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QFont


def _drug_info_url(med):
    """Build a MedlinePlus search URL for a medication dict.

    Brand name is preferred (it is what patients recognise) and the generic
    name is the fallback. Returns None when both are blank.

    Uses the NLM vsearch backend (the actual destination of the
    MedlinePlus homepage search form). The cleaner-looking
    medlineplus.gov/search.html does not exist (404).
    """
    term = (med.get("brand_name") or "").strip() or (med.get("generic_name") or "").strip()
    if not term:
        return None
    return QUrl(
        "https://vsearch.nlm.nih.gov/vivisimo/cgi-bin/query-meta"
        "?v%3Aproject=medlineplus"
        "&v%3Asources=medlineplus-bundle"
        f"&query={quote_plus(term)}"
    )


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
        # The previous version capped the right pane at maxWidth=450 — combined
        # with the section labels and the lookup button, that clipped the
        # detail content. Drop the cap, set a sensible minimum so neither
        # pane can be collapsed into nothing, and rely on the splitter
        # stretch factors to balance the two sides at any window width.
        right = QScrollArea()
        right.setWidgetResizable(True)
        right.setFrameShape(QFrame.Shape.NoFrame)
        right.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right.setMinimumWidth(380)
        detail = QWidget()
        self.detail_layout = QVBoxLayout(detail)
        self.detail_layout.setContentsMargins(8, 16, 16, 16)
        self.detail_layout.setSpacing(12)

        # Title row + compact "Look up" button. Putting the button on its own
        # row used to push everything off-screen; using a tight icon-style
        # label and giving the title the stretch keeps both visible at the
        # narrowest splitter sizes.
        title_row = QHBoxLayout()
        self.med_title = QLabel("Select a medication")
        self.med_title.setObjectName("heading")
        self.med_title.setWordWrap(True)
        title_row.addWidget(self.med_title, 1)

        self.lookup_btn = QPushButton("🔎 MedlinePlus")
        self.lookup_btn.setToolTip(
            "Open NIH MedlinePlus drug information for this medication "
            "in your default browser")
        self.lookup_btn.setVisible(False)
        self.lookup_btn.clicked.connect(self._open_drug_info)
        title_row.addWidget(self.lookup_btn, 0, Qt.AlignmentFlag.AlignTop)
        self.detail_layout.addLayout(title_row)

        self.med_generic = QLabel("")
        self.med_generic.setObjectName("subheading")
        self.detail_layout.addWidget(self.med_generic)
        self._current_med = None

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

        # Both children should be allowed to give up space on resize. Without
        # setChildrenCollapsible(False), a user could drag a pane shut by
        # accident and lose the medication detail entirely.
        left.setMinimumWidth(520)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        # Seed the initial split so the right pane gets enough room from the
        # first paint, instead of inheriting whatever the size hints land on.
        splitter.setSizes([840, 520])
        layout.addWidget(splitter)

    # Page size for the in-table view. After the FDA NDC bulk load the
    # medications table can hold 300k+ rows; loading them all and filtering
    # in Python (the pre-1.7.6-E behaviour) was the bottleneck. We now ask
    # the DB to filter and return one page; if the result set is larger
    # than the page, the footer prompts the user to narrow their search.
    PAGE_SIZE = 200

    def refresh_data(self):
        try:
            # Cheap; uses the index on drug_class. Capped at 200 entries —
            # if the user has more drug classes than that they can type the
            # class name into the search box instead.
            classes = self.db_manager.get_drug_class_options(limit=200)
            current = self.class_filter.currentText()
            self.class_filter.blockSignals(True)
            self.class_filter.clear()
            self.class_filter.addItem("All Classes")
            self.class_filter.addItems(classes)
            if current in classes:
                self.class_filter.setCurrentText(current)
            self.class_filter.blockSignals(False)

            self.apply_filter()
        except Exception as e:
            print(f"Medication refresh error: {e}")

    def apply_filter(self):
        search = self.search_input.text().strip() if hasattr(self, "search_input") else ""
        drug_class = self.class_filter.currentText() if hasattr(self, "class_filter") else "All Classes"
        schedule = self.schedule_filter.currentText() if hasattr(self, "schedule_filter") else "All Schedules"

        # Translate the UI's "Schedule II" / "Non-Controlled" labels into
        # the value the DB layer expects. Non-Controlled is a UI-only
        # convenience that does not have a single enum value, so we do it
        # client-side after the fact.
        sched_db = ""
        non_controlled_only = False
        schedule_map = {"Schedule II": "II", "Schedule III": "III",
                         "Schedule IV": "IV", "Schedule V": "V"}
        if schedule == "Non-Controlled":
            non_controlled_only = True
        elif schedule in schedule_map:
            sched_db = schedule_map[schedule]

        try:
            result = self.db_manager.search_medications(
                query=search,
                drug_class="" if drug_class == "All Classes" else drug_class,
                schedule=sched_db,
                limit=self.PAGE_SIZE,
                offset=0,
                include_total=True,
            )
        except Exception as e:
            print(f"Medication search error: {e}")
            return
        meds = result["medications"]
        total = result["total"]
        if non_controlled_only:
            meds = [m for m in meds if not m.get("is_controlled")]

        # Cache for on_med_selected / detail lookup; only the visible page,
        # not the full set.
        self.all_meds = meds
        self.populate_table(meds)

        # Footer summary — replaces the old aggregate stats line. The
        # avg-price + controlled-count totals were misleading once 300k
        # OTC products joined the dataset, so we now show what the user
        # actually sees on the current page plus the matching grand total.
        if total > self.PAGE_SIZE:
            note = (f"Showing {len(meds)} of {total} matches. "
                    f"Refine the search to narrow further.")
        else:
            note = f"Showing {len(meds)} of {total} matches."
        self.stats_label.setText(note)

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
        self._current_med = med
        self.med_title.setText(med.get("brand_name", ""))
        self.med_generic.setText(med.get("generic_name", ""))
        self.lookup_btn.setVisible(_drug_info_url(med) is not None)

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

    def _open_drug_info(self):
        if not self._current_med:
            return
        url = _drug_info_url(self._current_med)
        if url is None:
            return
        QDesktopServices.openUrl(url)

    def simulate_price_update(self):
        reply = QMessageBox.question(self, "Price Update",
            "Simulate a market price update (random +/-5% change) for the "
            "currently visible page only?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            for med in self.all_meds:
                # FDA bulk-loaded entries have no price; skip those instead of
                # multiplying None by a random float.
                awp = med.get("avg_wholesale_price") or 0
                retail = med.get("retail_price") or 0
                if not awp and not retail:
                    continue
                factor = 1 + random.uniform(-0.05, 0.05)
                self.db_manager.update_medication_prices(
                    med["id"],
                    round(awp * factor, 2),
                    round(retail * factor, 2))
            self.refresh_data()
            QMessageBox.information(self, "Success",
                "Medication prices updated for the visible page.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def export_csv(self):
        # Match the active filter, not just self.all_meds (which is one page).
        # Walk pages server-side so the export covers the full result set
        # even after a 300k-row FDA bulk load.
        path, _ = QFileDialog.getSaveFileName(self, "Export Medications", "medications.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            search = self.search_input.text().strip() if hasattr(self, "search_input") else ""
            drug_class = self.class_filter.currentText() if hasattr(self, "class_filter") else "All Classes"
            schedule = self.schedule_filter.currentText() if hasattr(self, "schedule_filter") else "All Schedules"
            sched_db = ""
            schedule_map = {"Schedule II": "II", "Schedule III": "III",
                             "Schedule IV": "IV", "Schedule V": "V"}
            if schedule in schedule_map:
                sched_db = schedule_map[schedule]
            non_controlled_only = (schedule == "Non-Controlled")

            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["NDC", "Brand Name", "Generic Name", "Manufacturer", "Class",
                                 "Schedule", "Route", "Form", "Strength", "AWP", "Retail Price",
                                 "Indications", "Contraindications", "Side Effects"])
                offset = 0
                page = 2000   # larger than the UI page; export should be fast
                written = 0
                while True:
                    batch = self.db_manager.search_medications(
                        query=search,
                        drug_class="" if drug_class == "All Classes" else drug_class,
                        schedule=sched_db,
                        limit=page, offset=offset)
                    if not batch:
                        break
                    for m in batch:
                        if non_controlled_only and m.get("is_controlled"):
                            continue
                        writer.writerow([
                            m.get("ndc_code"), m.get("brand_name"), m.get("generic_name"),
                            m.get("manufacturer"), m.get("drug_class"), m.get("schedule"),
                            m.get("route"), m.get("form"), m.get("strength"),
                            m.get("avg_wholesale_price"), m.get("retail_price"),
                            m.get("indications"), m.get("contraindications"), m.get("side_effects")
                        ])
                        written += 1
                    offset += len(batch)
                    if len(batch) < page:
                        break
            QMessageBox.information(self, "Success", f"Exported {written} medications to {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
