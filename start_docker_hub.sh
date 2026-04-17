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
#
# Override the image tag:
#   MEDPHARM_IMAGE_TAG=1.1.1 ./start_docker_hub.sh api
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
    docker compose -f "${SCRIPT_DIR}/docker-compose.hub.yml" down 2>/dev/null || true
    docker compose -f "${SCRIPT_DIR}/server/docker-compose.hub.yml" down 2>/dev/null || true
    log "All MedPharm containers stopped"
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
    read -p "  Select [1-4]: " choice
    case "$choice" in
        1) start_api ;;
        2) start_server ;;
        3) pull_only ;;
        4) stop_all ;;
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
    "")     interactive_menu ;;
    -h|--help)
        grep '^#' "$0" | sed 's/^# \?//' | head -40
        ;;
    *) fail "Unknown option: $1 (use: api, server, pull, stop, or no arg for menu)" ;;
esac
