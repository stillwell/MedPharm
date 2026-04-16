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
echo ""
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║  MedPharm ERP - Desktop Application                  ║"
echo "  ║                                                       ║"
echo "  ║  Doctor:       dr.carter / doctor123                  ║"
echo "  ║  Psychiatrist: dr.brooks / doctor123                  ║"
echo "  ║  Pharmacist:   pharm.davis / pharm123                 ║"
echo "  ║  Admin:        admin / admin123                       ║"
echo "  ║                                                       ║"
echo "  ║  © 2026 Enlightec Ltd.                                ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo ""
cd "${SCRIPT_DIR}"
python3 run_qt.py
