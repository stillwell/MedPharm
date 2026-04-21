#!/bin/bash
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# License: GNU General Public License v3.0
#
# API-only container entrypoint. Runs gunicorn with optional TLS.
#
# TLS behaviour (controlled by MEDPHARM_TLS_MODE):
#   auto     : self-signed cert auto-generated into $MEDPHARM_TLS_DIR if missing
#   require  : cert must be provided at $MEDPHARM_TLS_DIR (fail if absent)
#   disable  : plaintext HTTP on $MEDPHARM_PORT (legacy behaviour)
#
# When TLS is on, gunicorn binds 0.0.0.0:$MEDPHARM_PORT with --certfile/--keyfile.
set -e

TLS_DIR="${MEDPHARM_TLS_DIR:-/etc/ssl/medpharm}"
TLS_HOSTNAME="${MEDPHARM_TLS_HOSTNAME:-localhost}"
TLS_DAYS="${MEDPHARM_TLS_DAYS:-825}"
TLS_MODE="${MEDPHARM_TLS_MODE:-auto}"
PORT="${MEDPHARM_PORT:-8080}"
WORKERS="${MEDPHARM_WORKERS:-4}"
THREADS="${MEDPHARM_THREADS:-2}"

GUNICORN_ARGS=(
    "run_cloud:app"
    "--preload"
    "--bind" "0.0.0.0:${PORT}"
    "--workers" "${WORKERS}"
    "--threads" "${THREADS}"
    "--timeout" "120"
    "--access-logfile" "-"
    "--error-logfile" "-"
)

if [ "$TLS_MODE" != "disable" ]; then
    mkdir -p "$TLS_DIR"
    chmod 700 "$TLS_DIR" 2>/dev/null || true

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
    fi

    GUNICORN_ARGS+=(
        "--certfile" "$TLS_DIR/fullchain.pem"
        "--keyfile"  "$TLS_DIR/privkey.pem"
    )
    echo "  Starting MedPharm API on https://0.0.0.0:${PORT}"
else
    echo "  TLS disabled — starting MedPharm API on http://0.0.0.0:${PORT}"
fi

exec gunicorn "${GUNICORN_ARGS[@]}"
