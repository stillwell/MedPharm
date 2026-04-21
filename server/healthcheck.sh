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
#
# Docker / Kubernetes health probe — returns 0 iff /api/v1/health responds.
# Tries HTTPS first (TLS-enabled image default). Falls back to HTTP for
# plaintext variants. -k tolerates self-signed certs in dev installs.
set -e

if curl -skf https://localhost:443/api/v1/health > /dev/null 2>&1; then
    exit 0
fi

if curl -sf http://localhost:80/api/v1/health > /dev/null 2>&1; then
    exit 0
fi

exit 1
