#!/usr/bin/env python3
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
MedPharm ERP - Qt Desktop Application Launcher

Launches the PyQt6 desktop application for doctors and psychiatrists.
Initializes the SQLite database and seeds it with sample data on first run.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from database.seed_demo import seed_demo_data
from qt_app.main_window import MainWindow


DB_PATH = os.environ.get(
    "MEDPHARM_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "medpharm_erp.db"),
)
# When MEDPHARM_DATABASE_URL is set (e.g. a PostgreSQL URL) the desktop app
# attaches to that shared server database instead of its private SQLite file,
# so clinical staff see the same patients/prescriptions as the web portal, the
# REST API, and every mobile client. Unset = standalone single-file SQLite.
DATABASE_URL = os.environ.get("MEDPHARM_DATABASE_URL")


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("MedPharm ERP")
    app.setOrganizationName("MedPharm")
    app.setApplicationVersion("1.7.6")

    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    db_manager = DatabaseManager(db_path=DB_PATH, database_url=DATABASE_URL)
    db_manager.init_db()
    print(f"MedPharm ERP — connected to {db_manager.safe_target}")

    # seed_database() no-ops on a populated database, so a desktop client
    # pointed at an already-seeded shared server leaves it untouched; a fresh
    # standalone SQLite file still gets the demo data on first launch.
    seed_database(db_manager)
    # Layer the complete demo on top (symptoms/conditions catalogue, provider
    # NPIs, today's appointment board, full-lifecycle insurance claims).
    # Idempotent + additive, and a no-op on an empty/patient-free database.
    seed_demo_data(db_manager)

    window = MainWindow(db_manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
