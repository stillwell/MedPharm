# MedPharm ERP - Cloud API Server
# Docker container for deploying the REST API to cloud environments.
#
# Build:  docker build -t medpharm-api .
# Run:    docker run -p 8080:8080 -e MEDPHARM_JWT_SECRET=your-secret medpharm-api
#
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# License: GNU General Public License v3.0

FROM python:3.12-slim

LABEL maintainer="Enlightec Ltd. <info@enlightec.com>"
LABEL description="MedPharm ERP Cloud API Server"
LABEL version="1.0.0"

# Set environment defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MEDPHARM_HOST=0.0.0.0 \
    MEDPHARM_PORT=8080 \
    MEDPHARM_DB_PATH=/data/medpharm_erp.db

WORKDIR /app

# Install Python dependencies
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Copy application code
COPY medical_erp/ medical_erp/
COPY api/ medical_erp/api/
COPY database/ medical_erp/database/
COPY run_cloud.py .

# Create data directory for SQLite database
RUN mkdir -p /data

# Expose the API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/v1/health')" || exit 1

# Run with gunicorn in production
CMD ["gunicorn", "run_cloud:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
