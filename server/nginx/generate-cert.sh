#!/usr/bin/env bash
# MedPharm ERP - TLS certificate helper
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Licensed under the GNU General Public License v3.0 or later.
#
# For local development & staging only. In production, use a CA-issued
# certificate (Let's Encrypt, ACM, or your corporate PKI). Never ship a
# production deployment with a self-signed cert — browsers and mobile
# clients will refuse the connection and staff will be trained to click
# past warnings, which is a compliance failure mode in itself.

set -euo pipefail

OUT_DIR="${1:-/etc/ssl/medpharm}"
HOSTNAME="${2:-$(hostname -f 2>/dev/null || hostname)}"
DAYS="${3:-365}"

if [[ "$(id -u)" -ne 0 && ! -w "$(dirname "$OUT_DIR")" ]]; then
    echo "This script writes to ${OUT_DIR}. Run with sudo or choose a writable path." >&2
    echo "Usage: $0 [OUT_DIR] [HOSTNAME] [DAYS]" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"

KEY="$OUT_DIR/privkey.pem"
CRT="$OUT_DIR/fullchain.pem"

if [[ -f "$KEY" || -f "$CRT" ]]; then
    read -r -p "Certificate already exists in ${OUT_DIR}. Overwrite? [y/N] " yn
    [[ "${yn,,}" == "y" || "${yn,,}" == "yes" ]] || { echo "Aborting."; exit 1; }
fi

echo "Generating self-signed RSA-4096 certificate for ${HOSTNAME} (${DAYS} days)..."

openssl req -x509 -nodes -newkey rsa:4096 \
    -keyout "$KEY" -out "$CRT" -days "$DAYS" -sha256 \
    -subj "/CN=${HOSTNAME}/O=MedPharm ERP (self-signed)" \
    -addext "subjectAltName=DNS:${HOSTNAME},DNS:localhost,IP:127.0.0.1" \
    -addext "keyUsage=digitalSignature,keyEncipherment" \
    -addext "extendedKeyUsage=serverAuth"

chmod 600 "$KEY"
chmod 644 "$CRT"

echo
echo "  Key:  $KEY"
echo "  Cert: $CRT"
echo
echo "Point nginx at these with:"
echo "  ssl_certificate     ${CRT};"
echo "  ssl_certificate_key ${KEY};"
echo
echo "Reload nginx: sudo nginx -t && sudo systemctl reload nginx"
