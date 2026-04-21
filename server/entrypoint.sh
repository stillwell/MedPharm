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

TLS_DIR="${MEDPHARM_TLS_DIR:-/etc/ssl/medpharm}"
TLS_HOSTNAME="${MEDPHARM_TLS_HOSTNAME:-localhost}"
TLS_DAYS="${MEDPHARM_TLS_DAYS:-825}"
TLS_MODE="${MEDPHARM_TLS_MODE:-auto}"   # auto | require | disable

# ── Provision TLS certificates ─────────────────────────────────────────
# Priority:
#   1. User-mounted cert at $TLS_DIR/fullchain.pem + privkey.pem (CA-issued)
#   2. Self-signed generated on first boot (auto mode)
#   3. Fall back to plaintext nginx config (TLS_MODE=disable)

mkdir -p "$TLS_DIR"
chmod 700 "$TLS_DIR" 2>/dev/null || true

if [ "$TLS_MODE" != "disable" ]; then
    if [ -s "$TLS_DIR/fullchain.pem" ] && [ -s "$TLS_DIR/privkey.pem" ]; then
        echo "  TLS cert found at $TLS_DIR (provided)"
    elif [ "$TLS_MODE" = "require" ]; then
        echo "  ERROR: MEDPHARM_TLS_MODE=require but no cert at $TLS_DIR" >&2
        exit 1
    else
        echo "  Generating self-signed TLS cert for $TLS_HOSTNAME ($TLS_DAYS days)..."
        openssl req -x509 -nodes -newkey rsa:4096 \
            -keyout "$TLS_DIR/privkey.pem" \
            -out    "$TLS_DIR/fullchain.pem" \
            -days   "$TLS_DAYS" -sha256 \
            -subj "/CN=${TLS_HOSTNAME}/O=MedPharm ERP (self-signed)" \
            -addext "subjectAltName=DNS:${TLS_HOSTNAME},DNS:localhost,IP:127.0.0.1" \
            -addext "keyUsage=digitalSignature,keyEncipherment" \
            -addext "extendedKeyUsage=serverAuth" 2>/dev/null
        chmod 600 "$TLS_DIR/privkey.pem"
        chmod 644 "$TLS_DIR/fullchain.pem"
        echo "  Self-signed TLS cert ready. Mount a CA cert at $TLS_DIR for production."
    fi
    ln -sf /etc/nginx/sites-available/medpharm /etc/nginx/sites-enabled/medpharm
    SCHEME="https"
    PORT_HINT="443"
else
    echo "  TLS disabled (MEDPHARM_TLS_MODE=disable) — serving plain HTTP on port 80"
    ln -sf /etc/nginx/sites-available/medpharm-plain /etc/nginx/sites-enabled/medpharm
    SCHEME="http"
    PORT_HINT="80"
fi

echo ""
echo "  =================================================================="
echo "  MedPharm ERP Server - Ubuntu 24.04 LTS"
echo "  Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)"
echo "  =================================================================="
echo ""
echo "  Services:"
if [ "$TLS_MODE" != "disable" ]; then
    echo "    Nginx HTTPS (TLS) .......... port 443"
    echo "    Nginx HTTP -> 443 redirect . port 80"
else
    echo "    Nginx Reverse Proxy ........ port 80 (HTTP only)"
fi
echo "    Cloud REST API ............. port ${MEDPHARM_API_PORT:-8080}"
echo "    Patient Web Portal ......... port ${MEDPHARM_WEB_PORT:-5000}"
echo ""
echo "  Database: ${MEDPHARM_DB_PATH:-/data/medpharm_erp.db}"
echo "  Workers:  ${MEDPHARM_WORKERS:-4} (${MEDPHARM_THREADS:-2} threads each)"
echo ""
echo "  API Endpoints:"
echo "    ${SCHEME}://localhost:${PORT_HINT}/api/v1/health"
echo "    ${SCHEME}://localhost:${PORT_HINT}/api/v1/auth/login/patient"
echo "    ${SCHEME}://localhost:${PORT_HINT}/api/v1/auth/login/staff"
echo ""
echo "  Web Portal:"
echo "    ${SCHEME}://localhost:${PORT_HINT}/portal/"
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

# Validate nginx config before handing control to supervisord
nginx -t

# Execute the main command (supervisord)
exec "$@"
