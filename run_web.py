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

# run_web.py serves the portal directly with Flask's built-in server over plain
# HTTP. Browsers refuse to send a Secure-flagged cookie back over HTTP, which
# would wipe the session between GET /login and POST /login and surface as
# "CSRF token missing or invalid". Default the TLS-coupled cookie flags off
# unless the operator has explicitly opted in (the production server stack at
# server/Dockerfile keeps the secure default since it terminates TLS at nginx).
os.environ.setdefault("MEDPHARM_REQUIRE_TLS", "false")

from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from database.seed_demo import seed_demo_data
from web.app import create_app


DB_PATH = os.environ.get(
    "MEDPHARM_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "medpharm_erp.db"),
)
DATABASE_URL = os.environ.get("MEDPHARM_DATABASE_URL")

# Database setup (module-level so gunicorn can import run_web:app)
db_manager = DatabaseManager(db_path=DB_PATH, database_url=DATABASE_URL)
db_manager.init_db()
seed_database(db_manager)
# Complete the demo (symptoms/conditions, provider NPIs, today's appointments,
# insurance claims). Idempotent; no-ops on an empty/patient-free database.
seed_demo_data(db_manager)

# Create the Flask app (usable by gunicorn as run_web:app)
app = create_app(db_manager)


def main():
    print("=" * 60)
    print("  MedPharm ERP - Patient Web Portal")
    print("=" * 60)
    print(f"  Server running at: http://localhost:5000")
    print(f"  Database: {db_manager.safe_target}")
    print()
    print("  Sample patient portal accounts:")
    print("    Username: jsmith_portal  Password: patient123")
    print("    Username: mjohnson_portal  Password: patient123")
    print("    Username: ewilliams_portal  Password: patient123")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()
