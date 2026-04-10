#!/bin/bash
# MedPharm ERP - Cloud API Server Quick Start
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# License: GNU General Public License v3.0

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           MedPharm ERP - Cloud API Server                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import flask_cors" 2>/dev/null; then
    echo "Installing cloud dependencies..."
    pip install -r requirements-cloud.txt
fi

# Set defaults for development
export MEDPHARM_DEBUG=${MEDPHARM_DEBUG:-true}
export MEDPHARM_JWT_SECRET=${MEDPHARM_JWT_SECRET:-dev-secret-do-not-use-in-production}
export MEDPHARM_PORT=${MEDPHARM_PORT:-8080}

echo "Starting cloud API server on port $MEDPHARM_PORT..."
echo "API Base: http://localhost:$MEDPHARM_PORT/api/v1"
echo ""

python3 run_cloud.py
