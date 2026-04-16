#!/bin/bash
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

set -e

echo ""
echo "  =================================================================="
echo "  MedPharm ERP Server - Ubuntu 24.04 LTS"
echo "  Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)"
echo "  =================================================================="
echo ""
echo "  Services:"
echo "    Nginx Reverse Proxy ........ port 80"
echo "    Cloud REST API ............. port ${MEDPHARM_API_PORT:-8080}"
echo "    Patient Web Portal ......... port ${MEDPHARM_WEB_PORT:-5000}"
echo ""
echo "  Database: ${MEDPHARM_DB_PATH:-/data/medpharm_erp.db}"
echo "  Workers:  ${MEDPHARM_WORKERS:-4} (${MEDPHARM_THREADS:-2} threads each)"
echo ""
echo "  API Endpoints:"
echo "    http://localhost/api/v1/health"
echo "    http://localhost/api/v1/auth/login/patient"
echo "    http://localhost/api/v1/auth/login/staff"
echo ""
echo "  Web Portal:"
echo "    http://localhost/portal/"
echo ""
echo "  Credentials:"
echo "    Patient Portal:  jsmith_portal / patient123"
echo "    Staff API:       dr.carter / doctor123"
echo "    Admin:           admin / admin123"
echo ""
echo "  =================================================================="
echo ""

# Initialize database on first run
cd /opt/medpharm
export PYTHONPATH=/opt/medpharm

python3 -c "
import os, sys
sys.path.insert(0, '/opt/medpharm')
from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from database.seed_expanded import seed_expanded_data

db_path = os.environ.get('MEDPHARM_DB_PATH', '/data/medpharm_erp.db')
print(f'  Initializing database: {db_path}')
db_manager = DatabaseManager(db_path)
db_manager.init_db()
seed_database(db_manager)
seed_expanded_data(db_manager)
print('  Database ready.')
print()
"

# Ensure correct permissions on data directory
chown -R medpharm:medpharm /data 2>/dev/null || true

# Execute the main command (supervisord)
exec "$@"
