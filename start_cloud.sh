#!/usr/bin/env bash
# MedPharm ERP - Cloud API Server Quick Start
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# License: GNU General Public License v3.0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/venv/bin/activate" 2>/dev/null || true
export PYTHONPATH="${SCRIPT_DIR}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import flask_cors" 2>/dev/null; then
    echo "Installing cloud dependencies..."
    pip install -r "${SCRIPT_DIR}/requirements-cloud.txt"
fi

# Set defaults for development
export MEDPHARM_DB_PATH="${SCRIPT_DIR}/data/medpharm.db"
export MEDPHARM_DEBUG=${MEDPHARM_DEBUG:-true}
export MEDPHARM_JWT_SECRET=${MEDPHARM_JWT_SECRET:-dev-secret-do-not-use-in-production}
export MEDPHARM_PORT=${MEDPHARM_PORT:-8080}

echo ""
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║  MedPharm ERP - Cloud API Server                     ║"
echo "  ║  Running at: http://localhost:${MEDPHARM_PORT}                 ║"
echo "  ║  API Base: http://localhost:${MEDPHARM_PORT}/api/v1            ║"
echo "  ║                                                       ║"
echo "  ║  Patient Login: jsmith_portal / patient123            ║"
echo "  ║  Staff Login:   dr.carter / doctor123                 ║"
echo "  ║  Press Ctrl+C to stop                                 ║"
echo "  ║                                                       ║"
echo "  ║  © 2026 Enlightec Ltd.                                ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo ""

cd "${SCRIPT_DIR}"
python3 run_cloud.py
