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
MedPharm ERP - Analytics & Reporting Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QComboBox, QPushButton, QGridLayout
)
from PyQt6.QtCore import Qt

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib
    matplotlib.use("QtAgg")
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class AnalyticsWidget(QWidget):
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Analytics & Reports")
        title.setObjectName("heading")
        header_row.addWidget(title)
        header_row.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("primary_button")
        refresh_btn.setMinimumHeight(38)
        refresh_btn.clicked.connect(self.refresh_data)
        header_row.addWidget(refresh_btn)
        main_layout.addLayout(header_row)

        if not HAS_MATPLOTLIB:
            main_layout.addWidget(QLabel(
                "Matplotlib is required for charts.\nInstall with: pip install matplotlib"))
            main_layout.addStretch()
            scroll.setWidget(container)
            outer = QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.addWidget(scroll)
            return

        # Summary Stats
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(16)
        self.stat_cards = {}
        for key, label, color in [
            ("patients", "Total Patients", "#00BCD4"),
            ("prescriptions", "Active Prescriptions", "#43A047"),
            ("monthly_rev", "Monthly Revenue", "#7C4DFF"),
            ("top_med", "Top Prescribed", "#FB8C00"),
        ]:
            card = self._create_stat_card(label, "-", color)
            self.stat_cards[key] = card
            self.stats_layout.addWidget(card["frame"])
        main_layout.addLayout(self.stats_layout)

        # Charts grid
        grid = QGridLayout()
        grid.setSpacing(16)

        # Revenue Chart
        rev_frame = QFrame()
        rev_frame.setObjectName("card")
        rev_layout = QVBoxLayout(rev_frame)
        rev_title = QLabel("Monthly Revenue")
        rev_title.setObjectName("card_title")
        rev_layout.addWidget(rev_title)
        self.rev_figure = Figure(figsize=(6, 3), dpi=100, facecolor="#1e2129")
        self.rev_canvas = FigureCanvas(self.rev_figure)
        rev_layout.addWidget(self.rev_canvas)
        grid.addWidget(rev_frame, 0, 0)

        # Demographics Chart
        demo_frame = QFrame()
        demo_frame.setObjectName("card")
        demo_layout = QVBoxLayout(demo_frame)
        demo_title = QLabel("Patient Demographics")
        demo_title.setObjectName("card_title")
        demo_layout.addWidget(demo_title)
        self.demo_figure = Figure(figsize=(5, 3), dpi=100, facecolor="#1e2129")
        self.demo_canvas = FigureCanvas(self.demo_figure)
        demo_layout.addWidget(self.demo_canvas)
        grid.addWidget(demo_frame, 0, 1)

        # Top Medications Chart
        med_frame = QFrame()
        med_frame.setObjectName("card")
        med_layout = QVBoxLayout(med_frame)
        med_title = QLabel("Top Prescribed Medications")
        med_title.setObjectName("card_title")
        med_layout.addWidget(med_title)
        self.med_figure = Figure(figsize=(6, 3), dpi=100, facecolor="#1e2129")
        self.med_canvas = FigureCanvas(self.med_figure)
        med_layout.addWidget(self.med_canvas)
        grid.addWidget(med_frame, 1, 0)

        # Provider Workload
        prov_frame = QFrame()
        prov_frame.setObjectName("card")
        prov_layout = QVBoxLayout(prov_frame)
        prov_title = QLabel("Provider Activity")
        prov_title.setObjectName("card_title")
        prov_layout.addWidget(prov_title)
        self.prov_figure = Figure(figsize=(5, 3), dpi=100, facecolor="#1e2129")
        self.prov_canvas = FigureCanvas(self.prov_figure)
        prov_layout.addWidget(self.prov_canvas)
        grid.addWidget(prov_frame, 1, 1)

        main_layout.addLayout(grid)
        main_layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _create_stat_card(self, label, value, color):
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
        if not HAS_MATPLOTLIB:
            return
        try:
            stats = self.db_manager.get_dashboard_stats()
            self.stat_cards["patients"]["value_label"].setText(str(stats.get("patient_count", 0)))
            self.stat_cards["prescriptions"]["value_label"].setText(str(stats.get("active_prescriptions", 0)))
            self.stat_cards["monthly_rev"]["value_label"].setText(f"${stats.get('monthly_revenue', 0):,.2f}")

            top_meds = self.db_manager.get_top_medications(10)
            if top_meds:
                self.stat_cards["top_med"]["value_label"].setText(top_meds[0]["name"])

            self._draw_revenue_chart()
            self._draw_demographics_chart()
            self._draw_medications_chart(top_meds)
            self._draw_provider_chart()
        except Exception as e:
            print(f"Analytics refresh error: {e}")

    def _draw_revenue_chart(self):
        data = self.db_manager.get_revenue_by_month(12)
        self.rev_figure.clear()
        ax = self.rev_figure.add_subplot(111)
        ax.set_facecolor("#1e2129")

        months = [d["month"] for d in data]
        revenues = [d["revenue"] for d in data]

        bars = ax.bar(range(len(months)), revenues, color="#00BCD4", alpha=0.85)
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=45, ha="right", fontsize=8, color="#808080")
        ax.tick_params(axis="y", colors="#808080")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#2a2d35")
        ax.spines["bottom"].set_color("#2a2d35")
        ax.yaxis.set_major_formatter(lambda x, p: f"${x:,.0f}")
        self.rev_figure.tight_layout()
        self.rev_canvas.draw()

    def _draw_demographics_chart(self):
        data = self.db_manager.get_patient_demographics()
        self.demo_figure.clear()
        ax = self.demo_figure.add_subplot(111)
        ax.set_facecolor("#1e2129")

        labels = [k.title() for k, v in data.items() if v > 0]
        sizes = [v for v in data.values() if v > 0]
        colors = ["#00BCD4", "#FF5722", "#7C4DFF", "#43A047"]

        if sizes:
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct="%1.0f%%",
                colors=colors[:len(sizes)],
                textprops={"color": "#e0e0e0", "fontsize": 10}
            )
            for at in autotexts:
                at.set_color("#ffffff")
                at.set_fontweight("bold")
        self.demo_figure.tight_layout()
        self.demo_canvas.draw()

    def _draw_medications_chart(self, top_meds):
        self.med_figure.clear()
        ax = self.med_figure.add_subplot(111)
        ax.set_facecolor("#1e2129")

        if top_meds:
            names = [m["name"][:15] for m in reversed(top_meds)]
            counts = [m["count"] for m in reversed(top_meds)]

            ax.barh(range(len(names)), counts, color="#43A047", alpha=0.85)
            ax.set_yticks(range(len(names)))
            ax.set_yticklabels(names, fontsize=9, color="#e0e0e0")
            ax.tick_params(axis="x", colors="#808080")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#2a2d35")
            ax.spines["bottom"].set_color("#2a2d35")

        self.med_figure.tight_layout()
        self.med_canvas.draw()

    def _draw_provider_chart(self):
        self.prov_figure.clear()
        ax = self.prov_figure.add_subplot(111)
        ax.set_facecolor("#1e2129")

        try:
            providers = self.db_manager.get_providers()
            names = []
            rx_counts = []
            appt_counts = []
            for p in providers:
                names.append(p["display_title"])
                rxs = self.db_manager.get_prescriptions_by_prescriber(p["id"])
                rx_counts.append(len(rxs))
                from datetime import date, timedelta
                appts = self.db_manager.get_appointments(
                    provider_id=p["id"],
                    date_from=date.today() - timedelta(days=30),
                    date_to=date.today()
                )
                appt_counts.append(len(appts))

            if names:
                x = range(len(names))
                width = 0.35
                ax.bar([i - width/2 for i in x], rx_counts, width, label="Prescriptions", color="#00BCD4", alpha=0.85)
                ax.bar([i + width/2 for i in x], appt_counts, width, label="Appointments (30d)", color="#FB8C00", alpha=0.85)
                ax.set_xticks(list(x))
                ax.set_xticklabels(names, fontsize=9, color="#e0e0e0")
                ax.tick_params(axis="y", colors="#808080")
                ax.legend(facecolor="#1e2129", edgecolor="#2a2d35", labelcolor="#e0e0e0")
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["left"].set_color("#2a2d35")
                ax.spines["bottom"].set_color("#2a2d35")
        except Exception:
            pass

        self.prov_figure.tight_layout()
        self.prov_canvas.draw()
