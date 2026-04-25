#!/usr/bin/env bash
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
# ==============================================================================
# MedPharm ERP - Docker Hub Quick-Launch
#
# Pulls the pre-built MedPharm images directly from Docker Hub and starts
# the chosen deployment with docker compose. No local build step required.
#
# Docker Hub:
#   https://hub.docker.com/r/enlightec/medpharm-server   (full stack)
#   https://hub.docker.com/r/enlightec/medpharm-api      (REST API only)
#
# Usage:
#   ./start_docker_hub.sh              # Interactive: choose API-only or full stack
#   ./start_docker_hub.sh api          # API-only container (port 8080)
#   ./start_docker_hub.sh server       # Full stack (Nginx + API + Portal)
#   ./start_docker_hub.sh pull         # Pull latest images without starting
#   ./start_docker_hub.sh stop         # Stop running MedPharm containers
#   ./start_docker_hub.sh ngrok        # Start API + public ngrok tunnel
#                                      # (requires NGROK_AUTHTOKEN env var)
#
# Override the image tag:
#   MEDPHARM_IMAGE_TAG=1.7.5 ./start_docker_hub.sh api
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TAG="${MEDPHARM_IMAGE_TAG:-latest}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
fail() { echo -e "${RED}[✗]${NC} $*"; exit 1; }
info() { echo -e "${CYAN}[i]${NC} $*"; }

# ── Verify Docker & Compose ──────────────────────────────────────────────────

check_docker() {
    command -v docker >/dev/null 2>&1 \
        || fail "Docker not found. Install from https://docs.docker.com/get-docker/"
    docker compose version >/dev/null 2>&1 \
        || fail "Docker Compose plugin not found. Install the docker-compose-plugin package."
    docker info >/dev/null 2>&1 \
        || fail "Docker daemon is not running. Start Docker and try again."
}

# ── Deployment Modes ─────────────────────────────────────────────────────────

start_api() {
    info "Pulling enlightec/medpharm-api:${TAG} from Docker Hub..."
    docker pull "enlightec/medpharm-api:${TAG}"

    info "Starting API-only container (port 8080)..."
    MEDPHARM_IMAGE_TAG="${TAG}" docker compose \
        -f "${SCRIPT_DIR}/docker-compose.hub.yml" up -d

    log "MedPharm API is running"
    echo
    echo "  ╔═══════════════════════════════════════════════════════╗"
    echo "  ║  MedPharm ERP - Cloud API (Docker Hub)                ║"
    echo "  ║  Image: enlightec/medpharm-api:${TAG}"
    echo "  ║  API:   http://localhost:8080/api/v1                  ║"
    echo "  ║  Health: http://localhost:8080/api/v1/health          ║"
    echo "  ╚═══════════════════════════════════════════════════════╝"
    echo
    echo "  Logs:  docker compose -f docker-compose.hub.yml logs -f"
    echo "  Stop:  ./start_docker_hub.sh stop"
}

start_server() {
    info "Pulling enlightec/medpharm-server:${TAG} from Docker Hub..."
    docker pull "enlightec/medpharm-server:${TAG}"

    if [[ ! -f "${SCRIPT_DIR}/server/.env" ]]; then
        warn "server/.env not found — copying from .env.example"
        cp "${SCRIPT_DIR}/server/.env.example" "${SCRIPT_DIR}/server/.env"
        warn "Edit server/.env and replace JWT/SECRET values before production use"
    fi

    info "Starting full stack (Nginx + API + Portal)..."
    MEDPHARM_IMAGE_TAG="${TAG}" docker compose \
        --env-file "${SCRIPT_DIR}/server/.env" \
        -f "${SCRIPT_DIR}/server/docker-compose.hub.yml" up -d

    log "MedPharm Server is running"
    echo
    echo "  ╔════════════════════════════════════════════════════════╗"
    echo "  ║  MedPharm ERP - Full Stack (Docker Hub)                ║"
    echo "  ║  Image:  enlightec/medpharm-server:${TAG}"
    echo "  ║  API:    http://localhost/api/v1/health                ║"
    echo "  ║  Portal: http://localhost/portal/                      ║"
    echo "  ║  Direct API:    http://localhost:8080/                 ║"
    echo "  ║  Direct Portal: http://localhost:5000/                 ║"
    echo "  ╚════════════════════════════════════════════════════════╝"
    echo
    echo "  Logs:  docker compose -f server/docker-compose.hub.yml logs -f"
    echo "  Stop:  ./start_docker_hub.sh stop"
}

pull_only() {
    info "Pulling enlightec/medpharm-api:${TAG}..."
    docker pull "enlightec/medpharm-api:${TAG}"
    info "Pulling enlightec/medpharm-server:${TAG}..."
    docker pull "enlightec/medpharm-server:${TAG}"
    log "Both images pulled successfully"
    docker images --filter "reference=enlightec/medpharm-*" \
        --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"
}

stop_all() {
    info "Stopping MedPharm containers..."
    docker compose -f "${SCRIPT_DIR}/docker-compose.hub.yml" --profile ngrok down 2>/dev/null || true
    docker compose -f "${SCRIPT_DIR}/server/docker-compose.hub.yml" down 2>/dev/null || true
    log "All MedPharm containers stopped"
}

# ── ngrok tunnel (firewall traversal for mobile clients) ─────────────────────

start_ngrok() {
    if [[ -z "${NGROK_AUTHTOKEN:-}" ]]; then
        fail "NGROK_AUTHTOKEN is not set. Get a free token at https://dashboard.ngrok.com and re-run: NGROK_AUTHTOKEN=<token> ./start_docker_hub.sh ngrok"
    fi
    info "Bringing up the API container (if not already running)..."
    MEDPHARM_IMAGE_TAG="${TAG}" docker compose \
        -f "${SCRIPT_DIR}/docker-compose.hub.yml" up -d
    info "Starting ngrok tunnel container (profile: ngrok)..."
    NGROK_AUTHTOKEN="${NGROK_AUTHTOKEN}" \
    NGROK_REGION="${NGROK_REGION:-us}" \
    MEDPHARM_IMAGE_TAG="${TAG}" \
        docker compose -f "${SCRIPT_DIR}/docker-compose.hub.yml" \
            --profile ngrok up -d ngrok

    info "Waiting for tunnel public URL..."
    local url=""
    for _ in $(seq 1 30); do
        sleep 1
        url="$(docker exec medpharm-ngrok wget -qO- http://127.0.0.1:4040/api/tunnels 2>/dev/null \
            | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for t in d.get("tunnels", []):
    pu = t.get("public_url","")
    if pu.startswith("https://"):
        print(pu); break
' 2>/dev/null || true)"
        [[ -n "$url" ]] && break
    done

    if [[ -z "$url" ]]; then
        warn "Could not read public URL from the ngrok inspector; check 'docker compose logs ngrok'."
        return 1
    fi

    local api_url="${url%/}/api/v1"
    mkdir -p "${SCRIPT_DIR}/data"
    echo "$url" > "${SCRIPT_DIR}/data/ngrok_public_url.txt"
    cat > "${SCRIPT_DIR}/data/ngrok_client_config.json" <<JSON
{
  "api_base_url": "$api_url",
  "public_url": "$url",
  "issued_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "tunnel": "ngrok",
  "schema": 1
}
JSON
    if command -v qrencode >/dev/null 2>&1; then
        qrencode -o "${SCRIPT_DIR}/data/ngrok_qr.png" -s 8 -m 2 "$api_url" 2>/dev/null \
            && info "QR code: ${SCRIPT_DIR}/data/ngrok_qr.png"
    fi

    log "ngrok tunnel is live"
    echo
    echo "  ╔══════════════════════════════════════════════════════════════════╗"
    echo "  ║  MedPharm ERP - Public Tunnel (ngrok)                            ║"
    echo "  ╚══════════════════════════════════════════════════════════════════╝"
    echo "  Public URL:      $url"
    echo "  Client API base: $api_url"
    echo "  Inspector UI:    http://127.0.0.1:4040"
    echo
    echo "  Configure each client (Android/iOS scan QR; macOS/Windows paste URL):"
    echo "    ${SCRIPT_DIR}/data/ngrok_qr.png"
    echo "    ${SCRIPT_DIR}/data/ngrok_public_url.txt"
    echo
    echo "  Stop:  docker compose -f docker-compose.hub.yml --profile ngrok down"
}

# ── Interactive Menu ─────────────────────────────────────────────────────────

interactive_menu() {
    echo -e "${BOLD}${CYAN}"
    cat << 'BANNER'
    ╔════════════════════════════════════════════════════════════════╗
    ║  MedPharm ERP - Docker Hub Deployment                          ║
    ║  Pre-built images from https://hub.docker.com/u/enlightec      ║
    ╚════════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
    echo "  1) API only        (enlightec/medpharm-api)"
    echo "     Lightweight REST API for mobile and desktop clients"
    echo
    echo "  2) Full stack      (enlightec/medpharm-server)"
    echo "     Nginx + REST API + Patient Web Portal"
    echo
    echo "  3) Pull images only (no start)"
    echo
    echo "  4) Stop running containers"
    echo
    echo "  5) Start ngrok tunnel (exposes API to the public Internet)"
    echo "     Requires NGROK_AUTHTOKEN env var (free: https://dashboard.ngrok.com)"
    echo
    read -p "  Select [1-5]: " choice
    case "$choice" in
        1) start_api ;;
        2) start_server ;;
        3) pull_only ;;
        4) stop_all ;;
        5) start_ngrok ;;
        *) fail "Invalid selection" ;;
    esac
}

# ── Main ─────────────────────────────────────────────────────────────────────

check_docker

case "${1:-}" in
    api)    start_api ;;
    server) start_server ;;
    full)   start_server ;;
    pull)   pull_only ;;
    stop|down) stop_all ;;
    ngrok|tunnel) start_ngrok ;;
    "")     interactive_menu ;;
    -h|--help)
        grep '^#' "$0" | sed 's/^# \?//' | head -40
        ;;
    *) fail "Unknown option: $1 (use: api, server, pull, stop, ngrok, or no arg for menu)" ;;
esac
