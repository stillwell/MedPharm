#!/usr/bin/env bash
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/venv/bin/activate" 2>/dev/null || true
export PYTHONPATH="${SCRIPT_DIR}"
PORT="${1:-5000}"
echo ""
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║  MedPharm ERP - Patient Portal                       ║"
echo "  ║  Running at: http://localhost:${PORT}                  ║"
echo "  ║                                                       ║"
echo "  ║  Login:  jsmith_portal / patient123                   ║"
echo "  ║  Press Ctrl+C to stop                                 ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo ""
cd "${SCRIPT_DIR}"
python3 run_web.py "$PORT"
