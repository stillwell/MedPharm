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
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  MedPharm ERP - Uninstallation Script                                      ║
# ║  Medical & Pharmaceutical Enterprise Resource Planning System              ║
# ║                                                                            ║
# ║  Reverses what install.sh created:                                         ║
# ║    - Python virtual environment (venv/)                                    ║
# ║    - SQLite database (data/medpharm.db) and data/ directory                ║
# ║    - Install log (install.log) and stray test databases                    ║
# ║    - Python bytecode caches (__pycache__, *.pyc)                           ║
# ║    - Docker Hub containers, volumes, and images (opt-in)                   ║
# ║                                                                            ║
# ║  Leaves tracked source files, launcher scripts, and .env files alone.      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -euo pipefail

# ── Colors & Formatting ───────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
DB_DIR="${SCRIPT_DIR}/data"
DB_PATH="${DB_DIR}/medpharm.db"
INSTALL_LOG="${SCRIPT_DIR}/install.log"
UNINSTALL_LOG="${SCRIPT_DIR}/uninstall.log"
TMP_TEST_DB="${TMPDIR:-/tmp}/medpharm_test_install.db"

FORCE=false
KEEP_DATA=false
REMOVE_DOCKER_API=false
REMOVE_DOCKER_SERVER=false
REMOVE_DOCKER_VOLUMES=false
REMOVE_DOCKER_IMAGES=false
REMOVE_ALL=false
REMOVE_ENV_FILE=false

# ── Parse Arguments ──────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        -f|--force|--yes) FORCE=true ;;
        --keep-data) KEEP_DATA=true ;;
        --docker|--docker-api) REMOVE_DOCKER_API=true ;;
        --docker-server|--docker-full) REMOVE_DOCKER_SERVER=true ;;
        --docker-volumes) REMOVE_DOCKER_VOLUMES=true ;;
        --docker-images) REMOVE_DOCKER_IMAGES=true ;;
        --remove-env) REMOVE_ENV_FILE=true ;;
        --all)
            REMOVE_ALL=true
            REMOVE_DOCKER_API=true
            REMOVE_DOCKER_SERVER=true
            REMOVE_DOCKER_VOLUMES=true
            REMOVE_DOCKER_IMAGES=true
            REMOVE_ENV_FILE=true
            ;;
        --help|-h)
            cat <<HELP
Usage: ./uninstall.sh [OPTIONS]

Source install cleanup (default):
  Removes the Python virtual environment (venv/), the SQLite database
  (data/medpharm.db), install.log, and Python bytecode caches.

Options:
  -f, --force, --yes   Skip all confirmation prompts (for CI / scripting)
      --keep-data      Preserve data/medpharm.db (and data/ directory)
      --remove-env     Also remove server/.env (kept by default — contains secrets)

Docker Hub cleanup (opt-in — nothing Docker-related runs without these flags):
      --docker, --docker-api
                       Stop and remove the API-only container
                       (docker-compose.hub.yml, container: medpharm-api)
      --docker-server, --docker-full
                       Stop and remove the full-stack container
                       (server/docker-compose.hub.yml, container: medpharm-server)
      --docker-volumes Also remove named Docker volumes (medpharm-data,
                       medpharm-logs) — THIS DELETES PERSISTED DB DATA
      --docker-images  Also remove the enlightec/medpharm-api and
                       enlightec/medpharm-server images from the local cache

Convenience:
      --all            Equivalent to:
                       --docker --docker-server --docker-volumes
                       --docker-images --remove-env

Examples:
  ./uninstall.sh                             # Interactive: remove venv, DB, log
  ./uninstall.sh --force                     # Non-interactive source cleanup
  ./uninstall.sh --keep-data                 # Remove venv, keep DB
  ./uninstall.sh --docker --docker-volumes   # Tear down API-only container + volume
  ./uninstall.sh --all --force               # Scorched earth — no prompts

Notes:
  - Tracked source files (launcher scripts, .env.example, docs, etc.) are
    never touched. Use 'git clean -fdx' if you want a fully pristine tree.
  - server/.env is preserved by default since it typically contains the JWT
    and session secrets you generated. Pass --remove-env to delete it.
HELP
            exit 0
            ;;
        *)
            echo -e "${RED}[✗]${NC} Unknown option: $arg"
            echo "    Run './uninstall.sh --help' for usage."
            exit 1
            ;;
    esac
done

# Auto-detect non-interactive environments (CI, piped input, etc.)
if [[ ! -t 0 ]]; then
    FORCE=true
fi

# ── Helper Functions ──────────────────────────────────────────────────────────

log()    { echo -e "${GREEN}[✓]${NC} $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] [OK] $*" >> "$UNINSTALL_LOG"; }
warn()   { echo -e "${YELLOW}[!]${NC} $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $*" >> "$UNINSTALL_LOG"; }
fail()   { echo -e "${RED}[✗]${NC} $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] [FAIL] $*" >> "$UNINSTALL_LOG"; exit 1; }
info()   { echo -e "${BLUE}[i]${NC} $*"; }
skip()   { echo -e "${DIM}[-]${NC} $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SKIP] $*" >> "$UNINSTALL_LOG"; }
header() { echo -e "\n${CYAN}${BOLD}═══ $* ═══${NC}\n"; }

confirm() {
    local prompt="$1"
    if [[ "$FORCE" == "true" ]]; then
        return 0
    fi
    read -p "    ${prompt} (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

banner() {
    echo -e "${CYAN}${BOLD}"
    cat << 'BANNER'
    ╔═════════════════════════════════════════════════════════════════════╗
    ║                                                                     ║
    ║   ███╗   ███╗███████╗██████╗ ██████╗ ██╗  ██╗ █████╗ ██████╗ ███╗  ║
    ║   ████╗ ████║██╔════╝██╔══██╗██╔══██╗██║  ██║██╔══██╗██╔══██╗████║ ║
    ║   ██╔████╔██║█████╗  ██║  ██║██████╔╝███████║███████║██████╔╝██╔═╝ ║
    ║   ██║╚██╔╝██║██╔══╝  ██║  ██║██╔═══╝ ██╔══██║██╔══██║██╔══██╗     ║
    ║   ██║ ╚═╝ ██║███████╗██████╔╝██║     ██║  ██║██║  ██║██║  ██║     ║
    ║   ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ║
    ║                   U N I N S T A L L E R                             ║
    ║           Medical & Pharmaceutical Management v1.0                  ║
    ║                                                                     ║
    ╚═════════════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
}

# ── Removal Steps ─────────────────────────────────────────────────────────────

remove_venv() {
    header "Removing Python Virtual Environment"
    if [[ -d "$VENV_DIR" ]]; then
        info "Found: ${VENV_DIR}"
        if confirm "Delete virtual environment?"; then
            rm -rf "$VENV_DIR"
            log "Removed ${VENV_DIR}"
        else
            skip "Kept ${VENV_DIR}"
        fi
    else
        skip "No virtual environment at ${VENV_DIR}"
    fi
}

remove_database() {
    header "Removing SQLite Database"
    if [[ "$KEEP_DATA" == "true" ]]; then
        skip "Preserving database (--keep-data)"
        return
    fi

    if [[ -f "$DB_PATH" ]]; then
        info "Found: ${DB_PATH} ($(du -h "$DB_PATH" | cut -f1))"
        if confirm "Delete database? This erases all patient/prescription data."; then
            rm -f "$DB_PATH"
            log "Removed ${DB_PATH}"
        else
            skip "Kept ${DB_PATH}"
            return
        fi
    else
        skip "No database at ${DB_PATH}"
    fi

    # Remove data/ directory if empty (or if it only contained the .db)
    if [[ -d "$DB_DIR" ]] && [[ -z "$(ls -A "$DB_DIR" 2>/dev/null)" ]]; then
        rmdir "$DB_DIR"
        log "Removed empty ${DB_DIR}"
    elif [[ -d "$DB_DIR" ]]; then
        warn "${DB_DIR} still contains files — leaving directory intact"
    fi

    # Stray test database from install validation
    if [[ -f "$TMP_TEST_DB" ]]; then
        rm -f "$TMP_TEST_DB"
        log "Removed stray test database ${TMP_TEST_DB}"
    fi
}

remove_logs() {
    header "Removing Install Logs"
    if [[ -f "$INSTALL_LOG" ]]; then
        rm -f "$INSTALL_LOG"
        log "Removed ${INSTALL_LOG}"
    else
        skip "No install.log to remove"
    fi
}

remove_pycache() {
    header "Removing Python Bytecode Caches"
    local count
    count=$(find "$SCRIPT_DIR" -type d -name '__pycache__' -not -path '*/venv/*' 2>/dev/null | wc -l)
    if (( count > 0 )); then
        find "$SCRIPT_DIR" -type d -name '__pycache__' -not -path '*/venv/*' -exec rm -rf {} + 2>/dev/null || true
        log "Removed ${count} __pycache__ director$( (( count == 1 )) && echo y || echo ies)"
    else
        skip "No __pycache__ directories found"
    fi

    local pyc_count
    pyc_count=$(find "$SCRIPT_DIR" -type f -name '*.pyc' -not -path '*/venv/*' 2>/dev/null | wc -l)
    if (( pyc_count > 0 )); then
        find "$SCRIPT_DIR" -type f -name '*.pyc' -not -path '*/venv/*' -delete 2>/dev/null || true
        log "Removed ${pyc_count} stray .pyc file$( (( pyc_count == 1 )) && echo "" || echo s)"
    fi
}

remove_env_file() {
    header "Removing server/.env"
    local env_file="${SCRIPT_DIR}/server/.env"
    if [[ ! -f "$env_file" ]]; then
        skip "No server/.env to remove"
        return
    fi

    if [[ "$REMOVE_ENV_FILE" == "true" ]]; then
        if confirm "Delete server/.env? It contains your JWT/session secrets."; then
            rm -f "$env_file"
            log "Removed ${env_file}"
        else
            skip "Kept ${env_file}"
        fi
    else
        skip "Preserving ${env_file} (pass --remove-env to delete)"
    fi
}

# ── Docker Teardown ──────────────────────────────────────────────────────────

check_docker_available() {
    if ! command -v docker >/dev/null 2>&1; then
        warn "Docker CLI not found — cannot tear down containers/volumes/images"
        return 1
    fi
    if ! docker info >/dev/null 2>&1; then
        warn "Docker daemon is not running — cannot tear down containers/volumes/images"
        return 1
    fi
    return 0
}

compose_down() {
    local compose_file="$1"
    local label="$2"
    local extra_env=()

    if [[ ! -f "$compose_file" ]]; then
        skip "${label}: compose file missing (${compose_file})"
        return
    fi

    # The server compose needs its env file for variable substitution
    if [[ "$compose_file" == *"server/docker-compose.hub.yml" ]] && [[ -f "${SCRIPT_DIR}/server/.env" ]]; then
        extra_env=(--env-file "${SCRIPT_DIR}/server/.env")
    fi

    info "${label}: docker compose down"
    if docker compose "${extra_env[@]}" -f "$compose_file" down 2>>"$UNINSTALL_LOG"; then
        log "${label}: containers stopped and removed"
    else
        warn "${label}: docker compose down reported errors (see uninstall.log)"
    fi
}

remove_docker_api() {
    [[ "$REMOVE_DOCKER_API" == "true" ]] || return 0
    header "Tearing Down Docker API-Only Container"
    check_docker_available || return 0
    compose_down "${SCRIPT_DIR}/docker-compose.hub.yml" "medpharm-api"

    # Belt-and-braces: nuke the container by name if still present
    if docker ps -a --format '{{.Names}}' | grep -qx "medpharm-api"; then
        docker rm -f medpharm-api >/dev/null 2>&1 || true
        log "Force-removed lingering 'medpharm-api' container"
    fi
}

remove_docker_server() {
    [[ "$REMOVE_DOCKER_SERVER" == "true" ]] || return 0
    header "Tearing Down Docker Full-Stack Container"
    check_docker_available || return 0
    compose_down "${SCRIPT_DIR}/server/docker-compose.hub.yml" "medpharm-server"

    if docker ps -a --format '{{.Names}}' | grep -qx "medpharm-server"; then
        docker rm -f medpharm-server >/dev/null 2>&1 || true
        log "Force-removed lingering 'medpharm-server' container"
    fi
}

remove_docker_volumes() {
    [[ "$REMOVE_DOCKER_VOLUMES" == "true" ]] || return 0
    header "Removing Docker Named Volumes"
    check_docker_available || return 0

    warn "This deletes the persistent database volume — all Docker-side data will be lost."
    if ! confirm "Proceed with volume removal?"; then
        skip "Volumes preserved"
        return
    fi

    for vol in medpharm-data medpharm-logs medpharm_medpharm-data medpharm_medpharm-logs server_medpharm-data server_medpharm-logs; do
        if docker volume inspect "$vol" >/dev/null 2>&1; then
            if docker volume rm "$vol" >/dev/null 2>&1; then
                log "Removed volume ${vol}"
            else
                warn "Could not remove volume ${vol} (still in use?)"
            fi
        fi
    done
}

remove_docker_images() {
    [[ "$REMOVE_DOCKER_IMAGES" == "true" ]] || return 0
    header "Removing Docker Hub Images"
    check_docker_available || return 0

    if ! confirm "Remove enlightec/medpharm-api and enlightec/medpharm-server images?"; then
        skip "Images preserved"
        return
    fi

    for image in enlightec/medpharm-api enlightec/medpharm-server; do
        # Collect every locally cached tag for this repository
        local tags
        tags=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep "^${image}:" || true)
        if [[ -z "$tags" ]]; then
            skip "${image}: no local images"
            continue
        fi
        while IFS= read -r tag; do
            if docker rmi "$tag" >/dev/null 2>&1; then
                log "Removed image ${tag}"
            else
                warn "Could not remove image ${tag} (still referenced?)"
            fi
        done <<< "$tags"
    done
}

# ── Summary ───────────────────────────────────────────────────────────────────

print_summary() {
    echo -e "\n${GREEN}${BOLD}"
    cat << 'DONE'
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║          ✓ UNINSTALLATION COMPLETE                            ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
DONE
    echo -e "${NC}"

    echo -e "${BOLD}What was removed:${NC}"
    [[ ! -d "$VENV_DIR" ]] && echo -e "  ${GREEN}✓${NC} Python virtual environment" || echo -e "  ${DIM}-${NC} Virtual environment kept"
    [[ ! -f "$DB_PATH" ]] && echo -e "  ${GREEN}✓${NC} SQLite database"             || echo -e "  ${DIM}-${NC} Database kept"
    [[ ! -f "$INSTALL_LOG" ]] && echo -e "  ${GREEN}✓${NC} install.log"             || echo -e "  ${DIM}-${NC} install.log kept"
    echo

    echo -e "${BOLD}What was preserved:${NC}"
    echo -e "  ${DIM}•${NC} Source code and tracked launcher scripts"
    echo -e "  ${DIM}•${NC} server/.env $( [[ "$REMOVE_ENV_FILE" == "true" ]] && echo "(removed)" || echo "(preserved — contains secrets)")"
    echo -e "  ${DIM}•${NC} Docker containers/volumes/images unless --docker* flags were passed"
    echo

    echo -e "${BOLD}To reinstall:${NC}"
    echo -e "  ./install.sh --fresh"
    echo
    echo -e "${BOLD}For a fully pristine tree (removes ALL untracked + ignored files):${NC}"
    echo -e "  ${DIM}git clean -fdx${NC}"
    echo
    echo -e "${DIM}Log: ${UNINSTALL_LOG}${NC}\n"
}

# ── Confirmation Preamble ────────────────────────────────────────────────────

show_plan() {
    header "Uninstall Plan"
    echo -e "${BOLD}Working directory:${NC} ${SCRIPT_DIR}\n"

    echo -e "${BOLD}Will remove:${NC}"
    [[ -d "$VENV_DIR" ]]       && echo -e "  ${YELLOW}•${NC} Virtual environment: ${VENV_DIR}"
    if [[ "$KEEP_DATA" != "true" ]]; then
        [[ -f "$DB_PATH" ]]    && echo -e "  ${YELLOW}•${NC} Database:            ${DB_PATH}"
    fi
    [[ -f "$INSTALL_LOG" ]]    && echo -e "  ${YELLOW}•${NC} Install log:         ${INSTALL_LOG}"
    echo -e "  ${YELLOW}•${NC} Python bytecode caches (__pycache__, *.pyc)"

    if [[ "$REMOVE_DOCKER_API" == "true" ]]; then
        echo -e "  ${YELLOW}•${NC} Docker container:    medpharm-api (docker-compose.hub.yml)"
    fi
    if [[ "$REMOVE_DOCKER_SERVER" == "true" ]]; then
        echo -e "  ${YELLOW}•${NC} Docker container:    medpharm-server (server/docker-compose.hub.yml)"
    fi
    if [[ "$REMOVE_DOCKER_VOLUMES" == "true" ]]; then
        echo -e "  ${RED}•${NC} Docker volumes:      medpharm-data, medpharm-logs ${RED}(DELETES PERSISTENT DATA)${NC}"
    fi
    if [[ "$REMOVE_DOCKER_IMAGES" == "true" ]]; then
        echo -e "  ${YELLOW}•${NC} Docker images:       enlightec/medpharm-api, enlightec/medpharm-server"
    fi
    if [[ "$REMOVE_ENV_FILE" == "true" ]] && [[ -f "${SCRIPT_DIR}/server/.env" ]]; then
        echo -e "  ${YELLOW}•${NC} Env file:            server/.env"
    fi

    echo
    echo -e "${BOLD}Will preserve:${NC}"
    echo -e "  ${GREEN}•${NC} Source code, Dockerfiles, compose files, docs, launcher scripts"
    if [[ "$KEEP_DATA" == "true" ]]; then
        echo -e "  ${GREEN}•${NC} Database (--keep-data)"
    fi
    if [[ "$REMOVE_ENV_FILE" != "true" ]] && [[ -f "${SCRIPT_DIR}/server/.env" ]]; then
        echo -e "  ${GREEN}•${NC} server/.env (pass --remove-env to delete)"
    fi
    echo

    if [[ "$FORCE" != "true" ]]; then
        if ! confirm "Proceed with uninstall?"; then
            info "Aborted — nothing was changed."
            exit 0
        fi
    fi
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
    cd "$SCRIPT_DIR"
    echo "" > "$UNINSTALL_LOG"

    banner
    show_plan

    remove_venv
    remove_database
    remove_logs
    remove_pycache
    remove_env_file

    remove_docker_api
    remove_docker_server
    remove_docker_volumes
    remove_docker_images

    print_summary
}

main "$@"
