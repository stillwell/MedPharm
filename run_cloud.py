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
MedPharm ERP - Cloud API Server Launcher
Starts the REST API server for Android and mobile client access.
Can be deployed to any cloud platform (AWS, GCP, Azure, Heroku, DigitalOcean).

Usage:
    python run_cloud.py                    # Development mode (localhost:8080)
    gunicorn run_cloud:app -b 0.0.0.0:8080 # Production mode

Environment Variables:
    MEDPHARM_DB_PATH         - Path to SQLite database (default: medpharm_erp.db)
    MEDPHARM_SECRET_KEY      - Flask secret key (auto-generated if not set)
    MEDPHARM_JWT_SECRET      - JWT signing secret (change in production!)
    MEDPHARM_TOKEN_EXPIRY    - Access token lifetime in seconds (default: 86400)
    MEDPHARM_REFRESH_EXPIRY  - Refresh token lifetime in seconds (default: 604800)
    MEDPHARM_CORS_ORIGINS    - Allowed CORS origins (default: * for development)
    MEDPHARM_HOST            - Server bind host (default: 0.0.0.0)
    MEDPHARM_PORT            - Server bind port (default: 8080)
    MEDPHARM_DEBUG           - Enable debug mode (default: false)
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from database.seed_expanded import seed_expanded_data
from api.app import create_cloud_app

# Database setup
db_path = os.environ.get("MEDPHARM_DB_PATH", "medpharm_erp.db")
db_manager = DatabaseManager(db_path)
db_manager.init_db()

# Seed with sample data if empty, then expanded reference data
seed_database(db_manager)
seed_expanded_data(db_manager)

# Create the Flask app (usable by gunicorn as run_cloud:app)
app = create_cloud_app(db_manager)

if __name__ == "__main__":
    host = os.environ.get("MEDPHARM_HOST", "0.0.0.0")
    port = int(os.environ.get("MEDPHARM_PORT", 8080))
    debug = os.environ.get("MEDPHARM_DEBUG", "false").lower() in ("true", "1", "yes")

    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                MedPharm ERP - Cloud API Server                ║
║                                                               ║
║  REST API for Android & Mobile Clients                        ║
║  Server: http://{host}:{port:<5}                                  ║
║  API Base: http://{host}:{port:<5}/api/v1                         ║
║  Health: http://{host}:{port:<5}/api/v1/health                    ║
║                                                               ║
║  Debug Mode: {'ON ' if debug else 'OFF'}                                            ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    app.run(host=host, port=port, debug=debug)
