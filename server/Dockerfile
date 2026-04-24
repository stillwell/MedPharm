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
# MedPharm ERP - Ubuntu Server Docker Image
#
# Runs both the Cloud REST API (port 8080) and Patient Web Portal (port 5000)
# behind Nginx reverse proxy (port 80/443).
#
# Build:  docker build -t medpharm-server .
# Run:    docker run -p 80:80 -e MEDPHARM_JWT_SECRET=your-secret medpharm-server
# ==============================================================================

FROM ubuntu:24.04

LABEL maintainer="Andrew Stillwell <Andrew.Stillwell@enlightec.com>"
LABEL org.opencontainers.image.title="MedPharm ERP Server"
LABEL org.opencontainers.image.description="MedPharm ERP Cloud API & Web Portal on Ubuntu Server"
LABEL org.opencontainers.image.version="1.7.5"
LABEL org.opencontainers.image.vendor="Enlightec Ltd."
LABEL org.opencontainers.image.url="https://www.enlightec.com"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    supervisor \
    curl \
    sqlite3 \
    openssl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd -r -s /bin/false -m -d /opt/medpharm medpharm

# Set up application directory
WORKDIR /opt/medpharm

# Create Python virtual environment
RUN python3 -m venv /opt/medpharm/venv
ENV PATH="/opt/medpharm/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/medpharm/venv"

# Install Python dependencies
COPY server/requirements-server.txt /tmp/requirements-server.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements-server.txt \
    && rm /tmp/requirements-server.txt

# Copy application source code
COPY database/ /opt/medpharm/database/
COPY security/ /opt/medpharm/security/
COPY api/ /opt/medpharm/api/
COPY web/ /opt/medpharm/web/
COPY run_cloud.py /opt/medpharm/
COPY run_web.py /opt/medpharm/
COPY __init__.py /opt/medpharm/
COPY LICENSE /opt/medpharm/

# Copy server configuration files (TLS-enabled nginx by default)
COPY server/nginx/medpharm-tls.conf /etc/nginx/sites-available/medpharm
COPY server/nginx/medpharm.conf /etc/nginx/sites-available/medpharm-plain
COPY server/nginx/generate-cert.sh /opt/medpharm/generate-cert.sh
COPY server/supervisord.conf /etc/supervisor/conf.d/medpharm.conf
COPY server/entrypoint.sh /opt/medpharm/entrypoint.sh
COPY server/healthcheck.sh /opt/medpharm/healthcheck.sh

# Configure Nginx and TLS directories
RUN rm -f /etc/nginx/sites-enabled/default \
    && ln -s /etc/nginx/sites-available/medpharm /etc/nginx/sites-enabled/medpharm \
    && mkdir -p /var/log/medpharm /etc/ssl/medpharm /var/www/certbot \
    && chmod 700 /etc/ssl/medpharm

# Create data directory for SQLite database
RUN mkdir -p /data \
    && chown medpharm:medpharm /data

# Make scripts executable
RUN chmod +x /opt/medpharm/entrypoint.sh /opt/medpharm/healthcheck.sh /opt/medpharm/generate-cert.sh

# Set ownership
RUN chown -R medpharm:medpharm /opt/medpharm /var/log/medpharm

# Application environment variables
ENV PYTHONPATH=/opt/medpharm \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MEDPHARM_DB_PATH=/data/medpharm_erp.db \
    MEDPHARM_HOST=0.0.0.0 \
    MEDPHARM_API_PORT=8080 \
    MEDPHARM_WEB_PORT=5000 \
    MEDPHARM_WORKERS=4 \
    MEDPHARM_THREADS=2 \
    MEDPHARM_TLS_DIR=/etc/ssl/medpharm \
    MEDPHARM_TLS_HOSTNAME=localhost \
    MEDPHARM_TLS_DAYS=825 \
    MEDPHARM_TLS_MODE=auto

# Expose ports: HTTP redirect (80), HTTPS (443), API direct (8080), Web Portal direct (5000)
EXPOSE 80 443 8080 5000

# Health check via Nginx
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD /opt/medpharm/healthcheck.sh

# Volumes for persistent data, logs, and TLS certificates
VOLUME ["/data", "/var/log/medpharm", "/etc/ssl/medpharm"]

ENTRYPOINT ["/opt/medpharm/entrypoint.sh"]
CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
