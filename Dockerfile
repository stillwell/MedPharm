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

# ==============================================================================
# MedPharm ERP - Cloud API Server (Ubuntu)
#
# Lightweight image running the REST API only (no web portal or Nginx).
# For the full server stack with Nginx, use server/Dockerfile instead.
#
# Build:  docker build -t medpharm-api .
# Run:    docker run -p 8080:8080 -e MEDPHARM_JWT_SECRET=your-secret medpharm-api
# ==============================================================================

FROM ubuntu:24.04

LABEL maintainer="Andrew Stillwell <Andrew.Stillwell@enlightec.com>"
LABEL org.opencontainers.image.title="MedPharm ERP Cloud API"
LABEL org.opencontainers.image.description="MedPharm ERP REST API on Ubuntu Server"
LABEL org.opencontainers.image.version="1.6.0"
LABEL org.opencontainers.image.vendor="Enlightec Ltd."
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"

ENV DEBIAN_FRONTEND=noninteractive

# Install system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    sqlite3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd -r -s /bin/false -m -d /opt/medpharm medpharm

WORKDIR /opt/medpharm

# Create virtual environment
RUN python3 -m venv /opt/medpharm/venv
ENV PATH="/opt/medpharm/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/medpharm/venv"

# Install Python dependencies
COPY requirements-cloud.txt /tmp/requirements-cloud.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements-cloud.txt \
    && rm /tmp/requirements-cloud.txt

# Copy application code
COPY database/ /opt/medpharm/database/
COPY api/ /opt/medpharm/api/
COPY run_cloud.py /opt/medpharm/
COPY __init__.py /opt/medpharm/

# Create data directory for SQLite database
RUN mkdir -p /data && chown medpharm:medpharm /data

# Set ownership
RUN chown -R medpharm:medpharm /opt/medpharm

# Environment
ENV PYTHONPATH=/opt/medpharm \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MEDPHARM_HOST=0.0.0.0 \
    MEDPHARM_PORT=8080 \
    MEDPHARM_DB_PATH=/data/medpharm_erp.db

EXPOSE 8080

VOLUME ["/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8080/api/v1/health || exit 1

USER medpharm

# Run with gunicorn in production
CMD ["gunicorn", "run_cloud:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
