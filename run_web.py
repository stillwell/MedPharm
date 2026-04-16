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
MedPharm ERP - Web Portal Launcher

Launches the Flask web application for patient self-service portal.
Provides prescription viewing, bill pay, and medical record access.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from web.app import create_app


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medpharm_erp.db")


def main():
    db_manager = DatabaseManager(DB_PATH)
    db_manager.init_db()

    seed_database(db_manager)

    app = create_app(db_manager)

    print("=" * 60)
    print("  MedPharm ERP - Patient Web Portal")
    print("=" * 60)
    print(f"  Server running at: http://localhost:5000")
    print(f"  Database: {DB_PATH}")
    print()
    print("  Sample patient portal accounts:")
    print("    Username: jsmith_portal  Password: patient123")
    print("    Username: mjohnson_portal  Password: patient123")
    print("    Username: ewilliams_portal  Password: patient123")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()
