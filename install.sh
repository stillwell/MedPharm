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
# ║  MedPharm ERP - Installation Script                                        ║
# ║  Medical & Pharmaceutical Enterprise Resource Planning System              ║
# ║                                                                            ║
# ║  Supports: Ubuntu/Debian, Fedora/RHEL, macOS, Arch Linux                  ║
# ║  Python 3.10+ required                                                     ║
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
LOG_FILE="${SCRIPT_DIR}/install.log"
FRESH=false
INSTALL_DOCKER_API=false
INSTALL_DOCKER_SERVER=false
INSTALL_NGROK=false
START_NGROK=false
NGROK_LOGIN=false
NGROK_AUTHTOKEN_ARG="${NGROK_AUTHTOKEN:-}"
NGROK_PORT="${NGROK_PORT:-8080}"
NGROK_REGION="${NGROK_REGION:-}"
NGROK_DOMAIN="${NGROK_DOMAIN:-}"
DOCKER_IMAGE_TAG="${MEDPHARM_IMAGE_TAG:-latest}"

# Where the captured ngrok auth token is persisted on this host. Picked up
# automatically by start_ngrok.sh, start_docker_hub.sh, and the docker-compose
# `ngrok` profile so the token only has to be entered once.
NGROK_TOKEN_DIR="${HOME}/.config/medpharm"
NGROK_TOKEN_FILE="${NGROK_TOKEN_DIR}/ngrok.env"

# ── Parse Arguments ──────────────────────────────────────────────────────────
#
# --docker and --docker-server can be combined on the same command line to
# deploy both the API-only container AND the full-stack container at once.
# When combined, the full-stack container's direct API port is remapped from
# 8080 to 8081 to avoid conflicting with the API-only container on 8080.

for arg in "$@"; do
    case "$arg" in
        --fresh) FRESH=true ;;
        --docker|--docker-api) INSTALL_DOCKER_API=true ;;
        --docker-server|--docker-full) INSTALL_DOCKER_SERVER=true ;;
        --tag=*) DOCKER_IMAGE_TAG="${arg#--tag=}" ;;
        --ngrok) INSTALL_NGROK=true; START_NGROK=true ;;
        --install-ngrok) INSTALL_NGROK=true ;;
        --ngrok-login) INSTALL_NGROK=true; NGROK_LOGIN=true ;;
        --ngrok-authtoken=*|--ngrok-token=*) NGROK_AUTHTOKEN_ARG="${arg#*=}" ;;
        --ngrok-port=*) NGROK_PORT="${arg#*=}" ;;
        --ngrok-region=*) NGROK_REGION="${arg#*=}" ;;
        --ngrok-domain=*|--ngrok-hostname=*) NGROK_DOMAIN="${arg#*=}" ;;
        --update|--check-update)
            # Delegate to the standalone updater. Strip the --update flag so
            # update.sh doesn't see it; everything else (--yes, --check-only,
            # --no-backup, --branch=...) is forwarded verbatim.
            updater="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/update.sh"
            [[ -x "$updater" ]] || { echo "update.sh not found at $updater" >&2; exit 1; }
            forwarded=()
            for a in "$@"; do
                [[ "$a" == "--update" || "$a" == "--check-update" ]] && continue
                forwarded+=("$a")
            done
            exec "$updater" "${forwarded[@]}"
            ;;
        --help|-h)
            cat <<HELP
Usage: ./install.sh [OPTIONS]

Source install (default):
  --fresh             Recreate virtual environment and reinitialize database

Update existing install (delegates to ./update.sh):
  --update            Check github.com/stillwell/MedPharm for new commits and,
                      if any are found, prompt to back up the database and
                      fast-forward the local source tree
  --check-update      Same as --update (additional flags --yes, --check-only,
                      --no-backup, --branch=<ref> are forwarded to update.sh)

Pre-built Docker Hub images (no Python build required):
  --docker            Pull enlightec/medpharm-api and start the API-only
                      container (port 8080)
  --docker-api        Same as --docker
  --docker-server     Pull enlightec/medpharm-server and start the full stack
                      — Nginx + REST API + Patient Web Portal (port 80)
  --tag=<version>     Image tag to pull (default: latest)

Combined Docker Hub deployment:
  --docker --docker-server
                      Deploy BOTH the API-only container AND the full-stack
                      container on the same host. The full-stack container's
                      direct API port is remapped from 8080 to 8081 so it
                      does not conflict with the API-only container on 8080.
                      The full-stack Nginx entry point stays on port 80.

Remote access via ngrok (firewall / NAT traversal for mobile clients):
  --ngrok             Install the ngrok agent (if missing) AND immediately
                      start a tunnel against the local API after the rest of
                      the install completes
  --install-ngrok     Install the ngrok agent only — do not start a tunnel
  --ngrok-login       Open the ngrok dashboard in a browser, prompt for the
                      auth token (input hidden) and persist it forever in
                      ~/.config/medpharm/ngrok.env (mode 0600) AND in
                      ngrok's own config (~/.config/ngrok/ngrok.yml). The
                      saved token is auto-sourced by every launcher script
                      after that, so the user never has to paste it again.
  --ngrok-authtoken=<TOKEN>
                      Persist an ngrok auth token non-interactively (also
                      accepts NGROK_AUTHTOKEN env var). Skips the browser
                      login. Free token: https://dashboard.ngrok.com
  --ngrok-port=<N>    Local port to expose (default: 8080 — the API)
  --ngrok-region=<R>  Edge region: us | eu | ap | au | sa | jp | in
  --ngrok-domain=<D>  Pin a reserved ngrok domain (paid tiers)

Examples:
  ./install.sh                              # Source install (Python venv)
  ./install.sh --docker                     # API-only via Docker Hub
  ./install.sh --docker-server              # Full stack via Docker Hub
  ./install.sh --docker --docker-server     # Both (API + full stack) at once
  ./install.sh --docker --tag=1.7.6         # Pin to a specific released version
  ./install.sh --docker --ngrok --ngrok-authtoken=2abc...
                                            # API-only + immediate public tunnel
  ./install.sh --install-ngrok              # Just put ngrok on PATH
  ./install.sh --ngrok-login                # Browser-based token capture
  ./install.sh --docker --ngrok --ngrok-login
                                            # Full firewalled-server setup with
                                            # token captured interactively (no
                                            # need to copy/paste on the cmdline)

Docker Hub:
  https://hub.docker.com/r/enlightec/medpharm-api
  https://hub.docker.com/r/enlightec/medpharm-server
HELP
            exit 0
            ;;
    esac
done

# Auto-detect non-interactive environments (CI, piped input, etc.)
if [[ ! -t 0 ]]; then
    FRESH=true
fi

# ── Helper Functions ──────────────────────────────────────────────────────────

log()    { echo -e "${GREEN}[✓]${NC} $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] [OK] $*" >> "$LOG_FILE"; }
warn()   { echo -e "${YELLOW}[!]${NC} $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $*" >> "$LOG_FILE"; }
fail()   { echo -e "${RED}[✗]${NC} $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] [FAIL] $*" >> "$LOG_FILE"; exit 1; }
info()   { echo -e "${BLUE}[i]${NC} $*"; }
header() { echo -e "\n${CYAN}${BOLD}═══ $* ═══${NC}\n"; }

spinner() {
    local pid=$1 msg=$2
    local chars='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while kill -0 "$pid" 2>/dev/null; do
        for (( i=0; i<${#chars}; i++ )); do
            printf "\r${BLUE}[${chars:$i:1}]${NC} %s" "$msg"
            sleep 0.1
        done
    done
    printf "\r"
}

banner() {
    echo -e "${CYAN}${BOLD}"
    cat << 'BANNER'
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                                                                          ║
    ║  ███╗   ███╗███████╗██████╗ ██████╗ ██╗  ██╗ █████╗ ██████╗ ███╗   ███╗  ║
    ║  ████╗ ████║██╔════╝██╔══██╗██╔══██╗██║  ██║██╔══██╗██╔══██╗████╗ ████║  ║
    ║  ██╔████╔██║█████╗  ██║  ██║██████╔╝███████║███████║██████╔╝██╔████╔██║  ║
    ║  ██║╚██╔╝██║██╔══╝  ██║  ██║██╔═══╝ ██╔══██║██╔══██║██╔══██╗██║╚██╔╝██║  ║
    ║  ██║ ╚═╝ ██║███████╗██████╔╝██║     ██║  ██║██║  ██║██║  ██║██║ ╚═╝ ██║  ║
    ║  ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ║
    ║                                                                          ║
    ║                           E R P   S Y S T E M                            ║
    ║                Medical & Pharmaceutical Management v1.7.6                ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
}

# ── Docker Hub Install Mode ──────────────────────────────────────────────────
#
# When --docker or --docker-server is passed, skip the Python venv path entirely
# and pull the official MedPharm images from Docker Hub. Compose files at
# docker-compose.hub.yml (API only) and server/docker-compose.hub.yml (full
# stack) reference these images.

check_docker() {
    header "Checking Docker"
    command -v docker >/dev/null 2>&1 || {
        echo -e "${RED}[✗]${NC} Docker is required for --docker install modes."
        info "  Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    }
    docker compose version >/dev/null 2>&1 || {
        echo -e "${RED}[✗]${NC} Docker Compose plugin is required."
        info "  Install docker-compose-plugin (e.g., apt install docker-compose-plugin)"
        exit 1
    }
    docker info >/dev/null 2>&1 || fail "Docker daemon is not running"
    log "Docker $(docker --version | awk '{print $3}' | tr -d ',') detected"
    log "Docker Compose plugin available"
}

install_docker_api() {
    header "Installing MedPharm ERP — API (Docker Hub)"
    info "Image: enlightec/medpharm-api:${DOCKER_IMAGE_TAG}"
    info "Source: https://hub.docker.com/r/enlightec/medpharm-api"

    info "Pulling image..."
    docker pull "enlightec/medpharm-api:${DOCKER_IMAGE_TAG}" 2>&1 | tee -a "$LOG_FILE" \
        || fail "Failed to pull enlightec/medpharm-api:${DOCKER_IMAGE_TAG}"
    log "Image pulled"

    info "Starting container via docker-compose.hub.yml..."
    MEDPHARM_IMAGE_TAG="${DOCKER_IMAGE_TAG}" docker compose \
        -f "${SCRIPT_DIR}/docker-compose.hub.yml" up -d \
        || fail "docker compose up failed"
    log "Container running"

    print_docker_summary "api"
}

install_docker_server() {
    header "Installing MedPharm ERP — Full Stack (Docker Hub)"
    info "Image: enlightec/medpharm-server:${DOCKER_IMAGE_TAG}"
    info "Source: https://hub.docker.com/r/enlightec/medpharm-server"

    # Ensure a .env file exists for the server compose
    if [[ ! -f "${SCRIPT_DIR}/server/.env" ]]; then
        warn "server/.env not found — copying from server/.env.example"
        cp "${SCRIPT_DIR}/server/.env.example" "${SCRIPT_DIR}/server/.env"
        warn "Edit server/.env and replace JWT/SECRET values before production"
    fi

    # When the API-only container is also being installed, remap the full
    # stack's direct API host port from 8080 to 8081 to avoid a port clash
    # with the API-only container that owns 8080.
    local server_api_port="8080"
    if [[ "$INSTALL_DOCKER_API" == "true" ]]; then
        server_api_port="8081"
        export MEDPHARM_API_PORT="${server_api_port}"
        warn "Remapping full-stack direct API port 8080 → ${server_api_port} to avoid clash with --docker (API-only on 8080)"
    fi

    info "Pulling image..."
    docker pull "enlightec/medpharm-server:${DOCKER_IMAGE_TAG}" 2>&1 | tee -a "$LOG_FILE" \
        || fail "Failed to pull enlightec/medpharm-server:${DOCKER_IMAGE_TAG}"
    log "Image pulled"

    info "Starting container via server/docker-compose.hub.yml..."
    MEDPHARM_IMAGE_TAG="${DOCKER_IMAGE_TAG}" MEDPHARM_API_PORT="${server_api_port}" \
        docker compose \
        --env-file "${SCRIPT_DIR}/server/.env" \
        -f "${SCRIPT_DIR}/server/docker-compose.hub.yml" up -d \
        || fail "docker compose up failed"
    log "Container running"

    SERVER_API_PORT="${server_api_port}"
    print_docker_summary "server"
}

print_docker_summary() {
    local mode="$1"
    echo -e "\n${GREEN}${BOLD}"
    cat <<'DONE'
    ╔═══════════════════════════════════════════════════════════════╗
    ║          ✓ DOCKER HUB DEPLOYMENT COMPLETE                     ║
    ╚═══════════════════════════════════════════════════════════════╝
DONE
    echo -e "${NC}"

    if [[ "$mode" == "api" ]]; then
        echo -e "${BOLD}Endpoints (TLS enabled — self-signed by default):${NC}"
        echo -e "  API base:   https://localhost:8080/api/v1"
        echo -e "  Health:     https://localhost:8080/api/v1/health  ${DIM}(curl -k)${NC}\n"
        echo -e "${BOLD}Manage:${NC}"
        echo -e "  Logs:  docker compose -f docker-compose.hub.yml logs -f"
        echo -e "  Stop:  docker compose -f docker-compose.hub.yml down"
    else
        local api_direct_port="${SERVER_API_PORT:-8080}"
        echo -e "${BOLD}Endpoints (TLS enabled — self-signed by default):${NC}"
        echo -e "  API:            https://localhost/api/v1/health   ${DIM}(curl -k)${NC}"
        echo -e "  Patient Portal: https://localhost/portal/"
        echo -e "  HTTP -> HTTPS:  http://localhost/  (301 redirect)"
        echo -e "  API direct:     http://localhost:${api_direct_port}/  ${DIM}(plain, container-internal port 8080)${NC}"
        echo -e "  Portal direct:  http://localhost:5000/  ${DIM}(plain, container-internal port 5000)${NC}\n"
        echo -e "${BOLD}Manage:${NC}"
        echo -e "  Logs:  docker compose -f server/docker-compose.hub.yml logs -f"
        echo -e "  Stop:  docker compose -f server/docker-compose.hub.yml down"
    fi
    echo
    echo -e "${BOLD}TLS:${NC}"
    echo -e "  Self-signed cert auto-generated on first boot into the 'medpharm-tls' volume."
    echo -e "  Production: mount a CA-issued cert at /etc/ssl/medpharm/{fullchain,privkey}.pem"
    echo -e "  and set MEDPHARM_TLS_MODE=require in your .env."
    echo
    echo -e "${BOLD}Default Credentials:${NC}"
    echo -e "  Staff:   dr.carter / doctor123"
    echo -e "  Patient: jsmith_portal / patient123\n"
    echo -e "${DIM}Image tag: ${DOCKER_IMAGE_TAG}${NC}"
    echo -e "${DIM}Docker Hub: https://hub.docker.com/u/enlightec${NC}\n"
}

# ── ngrok install / launch ────────────────────────────────────────────────────
#
# Puts the ngrok agent on PATH (Debian/Ubuntu via the official APT repo, macOS
# via Homebrew, RHEL/Fedora via the YUM repo, fallback to a static-binary
# download into ~/.local/bin). Then optionally starts the tunnel via
# ./start_ngrok.sh, which captures the public URL into data/ for the clients.

# Open the user's default browser at the given URL. Best-effort, returns 0
# even when no opener is available so the caller can fall back to printing
# the URL for the user to navigate to manually.
open_url_in_browser() {
    local url="$1"
    if command -v xdg-open >/dev/null 2>&1; then
        (xdg-open "$url" >/dev/null 2>&1 &) || true
    elif command -v open >/dev/null 2>&1; then
        # macOS
        (open "$url" >/dev/null 2>&1 &) || true
    elif command -v sensible-browser >/dev/null 2>&1; then
        (sensible-browser "$url" >/dev/null 2>&1 &) || true
    elif [[ -n "${BROWSER:-}" ]]; then
        ("$BROWSER" "$url" >/dev/null 2>&1 &) || true
    elif command -v powershell.exe >/dev/null 2>&1; then
        # WSL → Windows browser
        (powershell.exe -NoProfile -Command "Start-Process '$url'" >/dev/null 2>&1 &) || true
    else
        return 1
    fi
}

# Save the captured token to ~/.config/medpharm/ngrok.env (mode 0600) so the
# launcher scripts and the docker-compose `ngrok` profile pick it up without
# the user having to copy/paste it again. Two-line file:
#   # comment
#   NGROK_AUTHTOKEN=...
persist_ngrok_token_to_env_file() {
    local token="$1"
    [[ -z "$token" ]] && return 0
    mkdir -p "$NGROK_TOKEN_DIR"
    chmod 700 "$NGROK_TOKEN_DIR" 2>/dev/null || true
    {
        echo "# MedPharm ERP — captured ngrok auth token"
        echo "# Generated $(date -u +%Y-%m-%dT%H:%M:%SZ) by install.sh"
        echo "# Sourced automatically by start_ngrok.sh, start_docker_hub.sh,"
        echo "# and the docker-compose ngrok profile. To rotate, re-run:"
        echo "#   ./install.sh --ngrok-login"
        echo "NGROK_AUTHTOKEN=$token"
    } >"$NGROK_TOKEN_FILE"
    chmod 600 "$NGROK_TOKEN_FILE"
    log "Persisted token at $NGROK_TOKEN_FILE (mode 0600)"
}

# Interactive ngrok login flow:
#   1. Open the dashboard token page in the user's browser (or print the URL)
#   2. Read-prompt the user to paste the token (input hidden, no echo)
#   3. Save it via `ngrok config add-authtoken` AND in $NGROK_TOKEN_FILE
#
# ngrok intentionally does not expose a headless OAuth flow for tokens, so
# the dashboard-paste handshake is the supported path. We never log the
# token to install.log.
ngrok_login_and_capture_token() {
    header "ngrok login — capture API token"
    command -v ngrok >/dev/null 2>&1 \
        || fail "ngrok must be installed before --ngrok-login (run with --install-ngrok first)"

    local dashboard_url="https://dashboard.ngrok.com/get-started/your-authtoken"
    local signup_url="https://dashboard.ngrok.com/signup"

    info "Opening the ngrok auth-token page in your browser:"
    info "  $dashboard_url"
    info ""
    info "If you do not have an ngrok account yet, sign up first at:"
    info "  $signup_url"
    info ""
    info "When the page loads, copy the token shown in the gray code box."
    info "Then return to this terminal."
    echo

    open_url_in_browser "$dashboard_url" \
        || warn "Could not auto-open a browser. Visit the URL above manually."

    # Stop the install from racing the user — let them navigate to the page.
    info "Press <Enter> once the page is open and the token is on your clipboard..."
    if [[ -t 0 ]]; then read -r _; else echo "(non-interactive shell — skipping wait)"; fi

    local token=""
    local attempts=0
    while [[ -z "$token" && $attempts -lt 5 ]]; do
        attempts=$((attempts + 1))
        if [[ ! -t 0 ]]; then
            warn "Cannot prompt for a token in a non-interactive shell. Either pass --ngrok-authtoken=<TOKEN> or set NGROK_AUTHTOKEN in the environment."
            return 1
        fi
        # -s suppresses echo so the token stays off the screen / scrollback
        echo -n "  Paste the ngrok auth token (input hidden): "
        read -rs token
        echo
        token="$(echo -n "$token" | tr -d '[:space:]')"

        if [[ -z "$token" ]]; then
            warn "Empty input. Try again or press Ctrl-C to skip."
            continue
        fi

        # ngrok tokens are typically 40-50 chars of base64 / hex with an
        # optional underscore separating an account id from a secret. We
        # only sanity-check length here and let `ngrok config add-authtoken`
        # do the real verification.
        if [[ ${#token} -lt 20 ]]; then
            warn "That doesn't look like a valid ngrok token (only ${#token} chars). Try again."
            token=""
            continue
        fi
    done

    [[ -z "$token" ]] && fail "Did not receive a usable token after $attempts attempts"

    info "Storing token via 'ngrok config add-authtoken'..."
    if ngrok config add-authtoken "$token" >/dev/null 2>&1; then
        log "Token saved in ngrok's config (~/.config/ngrok/ngrok.yml)"
    else
        warn "ngrok rejected the token. Double-check it on the dashboard and re-run --ngrok-login."
        return 1
    fi

    persist_ngrok_token_to_env_file "$token"

    NGROK_AUTHTOKEN_ARG="$token"
    export NGROK_AUTHTOKEN="$token"
    return 0
}

install_ngrok() {
    header "Installing ngrok agent"
    if command -v ngrok >/dev/null 2>&1; then
        log "ngrok already installed: $(ngrok --version 2>&1 | head -1)"
        return 0
    fi

    local kernel uname_arch
    kernel="$(uname -s)"
    uname_arch="$(uname -m)"

    if [[ "$kernel" == "Darwin" ]]; then
        if command -v brew >/dev/null 2>&1; then
            info "Installing ngrok via Homebrew (brew install ngrok/ngrok/ngrok)..."
            brew install ngrok/ngrok/ngrok 2>&1 | tee -a "$LOG_FILE" \
                || warn "Homebrew install failed — falling back to direct download"
        else
            warn "Homebrew not found; falling back to direct download"
        fi
    elif [[ -f /etc/debian_version ]] && command -v apt-get >/dev/null 2>&1; then
        info "Adding ngrok APT repo and installing via apt..."
        if [[ ! -f /etc/apt/sources.list.d/ngrok.list ]]; then
            curl -fsSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
                | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
                || warn "Could not fetch ngrok APT GPG key"
            echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
                | sudo tee /etc/apt/sources.list.d/ngrok.list >/dev/null \
                || warn "Could not write /etc/apt/sources.list.d/ngrok.list"
        fi
        sudo apt-get update -y >>"$LOG_FILE" 2>&1 \
            && sudo apt-get install -y ngrok >>"$LOG_FILE" 2>&1 \
            || warn "apt install ngrok failed — falling back to direct download"
    elif [[ -f /etc/fedora-release || -f /etc/redhat-release ]]; then
        info "Adding ngrok YUM repo and installing via dnf/yum..."
        local ngrok_repo=/etc/yum.repos.d/ngrok.repo
        if [[ ! -f "$ngrok_repo" ]]; then
            sudo tee "$ngrok_repo" >/dev/null <<'REPO'
[ngrok]
name=ngrok
baseurl=https://ngrok-agent.s3.amazonaws.com/rpm
enabled=1
gpgcheck=0
REPO
        fi
        if command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y ngrok >>"$LOG_FILE" 2>&1 \
                || warn "dnf install ngrok failed — falling back to direct download"
        else
            sudo yum install -y ngrok >>"$LOG_FILE" 2>&1 \
                || warn "yum install ngrok failed — falling back to direct download"
        fi
    fi

    # Fallback: static binary into ~/.local/bin
    if ! command -v ngrok >/dev/null 2>&1; then
        local arch tarurl tmpdir
        case "$uname_arch" in
            x86_64|amd64) arch="amd64" ;;
            aarch64|arm64) arch="arm64" ;;
            armv7l) arch="arm" ;;
            *) fail "Unsupported CPU arch for ngrok: $uname_arch" ;;
        esac
        local osdir
        if [[ "$kernel" == "Darwin" ]]; then osdir="darwin"; else osdir="linux"; fi
        tarurl="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-${osdir}-${arch}.tgz"

        info "Downloading static ngrok binary from $tarurl"
        tmpdir="$(mktemp -d)"
        if curl -fsSL "$tarurl" -o "$tmpdir/ngrok.tgz" 2>>"$LOG_FILE"; then
            tar -xzf "$tmpdir/ngrok.tgz" -C "$tmpdir" >>"$LOG_FILE" 2>&1
            mkdir -p "$HOME/.local/bin"
            mv "$tmpdir/ngrok" "$HOME/.local/bin/ngrok"
            chmod +x "$HOME/.local/bin/ngrok"
            rm -rf "$tmpdir"
            export PATH="$HOME/.local/bin:$PATH"
            warn "ngrok installed to $HOME/.local/bin — make sure that directory is on your PATH"
        else
            rm -rf "$tmpdir"
            fail "Could not download ngrok from $tarurl"
        fi
    fi

    log "ngrok installed: $(ngrok --version 2>&1 | head -1)"

    if [[ -n "$NGROK_AUTHTOKEN_ARG" ]]; then
        info "Persisting ngrok auth token..."
        if ngrok config add-authtoken "$NGROK_AUTHTOKEN_ARG" >>"$LOG_FILE" 2>&1; then
            log "Auth token saved to ngrok config"
            persist_ngrok_token_to_env_file "$NGROK_AUTHTOKEN_ARG"
        else
            warn "Saving auth token failed — token may be invalid"
        fi
    fi
}

start_ngrok_tunnel() {
    header "Starting ngrok tunnel"
    local script="${SCRIPT_DIR}/start_ngrok.sh"
    [[ -x "$script" ]] || fail "start_ngrok.sh not found or not executable"

    local args=()
    [[ -n "$NGROK_PORT" ]]   && args+=("--port=$NGROK_PORT")
    [[ -n "$NGROK_REGION" ]] && args+=("--region=$NGROK_REGION")
    [[ -n "$NGROK_DOMAIN" ]] && args+=("--domain=$NGROK_DOMAIN")
    [[ -n "$NGROK_AUTHTOKEN_ARG" ]] && args+=("--authtoken=$NGROK_AUTHTOKEN_ARG")

    NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN_ARG" "$script" "${args[@]}" \
        || warn "ngrok tunnel did not come up — see data/ngrok.log for details"
}

# ── Detect OS & Package Manager ───────────────────────────────────────────────

detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MGR="brew"
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
        PKG_MGR="apt"
    elif [[ -f /etc/fedora-release ]]; then
        OS="fedora"
        PKG_MGR="dnf"
    elif [[ -f /etc/arch-release ]]; then
        OS="arch"
        PKG_MGR="pacman"
    elif [[ -f /etc/redhat-release ]]; then
        OS="rhel"
        PKG_MGR="yum"
    else
        OS="unknown"
        PKG_MGR="unknown"
    fi
    log "Detected OS: ${OS} (package manager: ${PKG_MGR})"
}

# ── Check Python Version ─────────────────────────────────────────────────────

check_python() {
    header "Checking Python Installation"

    local python_cmd=""
    for cmd in python3.12 python3.11 python3.10 python3; do
        if command -v "$cmd" &>/dev/null; then
            python_cmd="$cmd"
            break
        fi
    done

    if [[ -z "$python_cmd" ]]; then
        echo -e "${RED}[✗]${NC} Python 3.10+ is required but not found. Install it first:"
        info "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
        info "  Fedora:        sudo dnf install python3 python3-pip"
        info "  macOS:         brew install python@3.12"
        info "  Arch:          sudo pacman -S python python-pip"
        exit 1
    fi

    PYTHON="$python_cmd"
    PYTHON_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")

    if (( PYTHON_MAJOR < 3 || (PYTHON_MAJOR == 3 && PYTHON_MINOR < 10) )); then
        fail "Python 3.10+ required, found ${PYTHON_VERSION}"
    fi

    log "Python ${PYTHON_VERSION} found at $(which "$PYTHON")"
}

# ── Install System Dependencies ───────────────────────────────────────────────

install_system_deps() {
    header "Checking System Dependencies"

    local need_install=false

    # Check for venv support
    if ! "$PYTHON" -c "import venv" 2>/dev/null; then
        need_install=true
    fi

    if [[ "$need_install" == "true" ]]; then
        warn "Some system packages are missing. Attempting to install..."
        case "$PKG_MGR" in
            apt)
                if command -v sudo &>/dev/null; then
                    sudo apt update -qq 2>/dev/null
                    sudo apt install -y -qq "python${PYTHON_VERSION}-venv" python3-pip python3-dev 2>/dev/null || true
                else
                    warn "Cannot install system packages without sudo. You may need to run:"
                    info "  apt install python${PYTHON_VERSION}-venv python3-pip"
                fi
                ;;
            dnf)
                sudo dnf install -y python3-pip python3-devel 2>/dev/null || true
                ;;
            pacman)
                sudo pacman -S --noconfirm python-pip 2>/dev/null || true
                ;;
            brew)
                brew install python@3.12 2>/dev/null || true
                ;;
        esac
    fi

    log "System dependencies verified"
}

# ── Create Virtual Environment ────────────────────────────────────────────────

setup_venv() {
    header "Setting Up Virtual Environment"

    if [[ -d "$VENV_DIR" ]]; then
        if [[ "$FRESH" == "true" ]]; then
            warn "Removing existing virtual environment (--fresh)"
            rm -rf "$VENV_DIR"
        else
            warn "Existing virtual environment found at ${VENV_DIR}"
            read -p "    Recreate it? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -rf "$VENV_DIR"
            else
                log "Using existing virtual environment"
                source "${VENV_DIR}/bin/activate"
                return
            fi
        fi
    fi

    info "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR" 2>/dev/null || {
        warn "venv module not available. Trying with --without-pip..."
        "$PYTHON" -m venv --without-pip "$VENV_DIR" 2>/dev/null || {
            echo -e "${RED}[✗]${NC} Cannot create virtual environment. Install python3-venv:"
            info "  sudo apt install python${PYTHON_VERSION}-venv"
            exit 1
        }
    }

    source "${VENV_DIR}/bin/activate"
    log "Virtual environment created at ${VENV_DIR}"

    # Upgrade pip
    info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel -q 2>/dev/null || true
    log "pip upgraded"
}

# ── Install Python Dependencies ───────────────────────────────────────────────

install_python_deps() {
    header "Installing Python Dependencies"

    # Core dependencies
    local core_deps=(
        "Flask>=3.0"
        "SQLAlchemy>=2.0"
        "Werkzeug>=3.0"
        "flask-cors>=4.0"
    )

    # Analytics dependencies
    local analytics_deps=(
        "matplotlib>=3.8"
        "numpy>=1.24"
    )

    # Qt desktop dependencies
    local qt_deps=(
        "PyQt6>=6.6"
    )

    # Documentation dependencies
    local doc_deps=(
        "reportlab>=4.0"
    )

    info "Installing core dependencies..."
    pip install -q "${core_deps[@]}" 2>&1 | tee -a "$LOG_FILE" | grep -v "already satisfied" || true
    log "Core dependencies installed (Flask, SQLAlchemy, Werkzeug, flask-cors)"

    info "Installing analytics dependencies..."
    pip install -q "${analytics_deps[@]}" 2>&1 | tee -a "$LOG_FILE" | grep -v "already satisfied" || true
    log "Analytics dependencies installed (matplotlib, numpy)"

    info "Installing Qt desktop dependencies..."
    pip install -q "${qt_deps[@]}" 2>&1 | tee -a "$LOG_FILE" | { grep -v "already satisfied" || true; } || {
        warn "PyQt6 installation failed. The Qt desktop app requires PyQt6."
        warn "The web portal will still work without it."
        warn "To install later: pip install PyQt6"
    }

    info "Installing documentation dependencies..."
    pip install -q "${doc_deps[@]}" 2>&1 | tee -a "$LOG_FILE" | { grep -v "already satisfied" || true; } || {
        warn "reportlab installation failed. PDF generation will not be available."
    }

    log "All Python dependencies installed"
}

# ── Initialize Database ───────────────────────────────────────────────────────

init_database() {
    header "Initializing Database"

    mkdir -p "$DB_DIR"

    if [[ -f "$DB_PATH" ]]; then
        if [[ "$FRESH" == "true" ]]; then
            warn "Removing existing database (--fresh)"
            rm -f "$DB_PATH"
        else
            warn "Database already exists at ${DB_PATH}"
            read -p "    Reinitialize with fresh seed data? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -f "$DB_PATH"
                info "Old database removed"
            else
                log "Keeping existing database"
                return
            fi
        fi
    fi

    info "Creating database schema and seeding data..."
    "$PYTHON" -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')
from database.db_manager import DatabaseManager
from database.seed_data import seed_database

dm = DatabaseManager('${DB_PATH}')
dm.init_db()
seed_database(dm)
print('Database schema created and seed data loaded.')
" 2>&1 || fail "Database initialization failed"

    log "Database initialized at ${DB_PATH}"
    info "  - 15 sample patients"
    info "  - 55 real medications with FDA data"
    info "  - 24 drug-drug interactions"
    info "  - 5 staff users (doctors, psychiatrist, pharmacist, admin)"
    info "  - 12 active prescriptions"
    info "  - 8 invoices with payment history"
    info "  - Medical records, vitals, diagnoses, allergies"
}

# ── Create Launcher Scripts ───────────────────────────────────────────────────

create_launchers() {
    header "Creating Launcher Scripts"

    # Fallback launcher templates used only when the tracked launcher is
    # missing from the working tree. These intentionally carry the same GPL
    # header as the rest of the project so regenerated files stay
    # license-consistent with the repo.
    #
    # The tracked versions in the repo are richer (extra env setup, dep
    # checks, etc.) — when they are already present, preserve them instead
    # of clobbering with a minimal rewrite.

    _write_launcher_if_missing() {
        local path="$1"
        local name
        name="$(basename "$path")"
        if [[ -f "$path" ]]; then
            log "Preserving existing ${name}"
            chmod +x "$path" 2>/dev/null || true
            return
        fi
        shift
        "$@" > "$path"
        chmod +x "$path"
        log "Created ${name}"
    }

    _launcher_header() {
        cat <<'HDR'
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

HDR
    }

    _web_launcher() {
        _launcher_header
        cat <<'LAUNCHER'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/venv/bin/activate" 2>/dev/null || true
export PYTHONPATH="${SCRIPT_DIR}"
PORT="${1:-5000}"
echo ""
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║  MedPharm ERP - Patient Portal                       ║"
echo "  ║  Running at: http://localhost:${PORT}                  ║"
echo "  ║                                                       ║"
echo "  ║  Login:  jsmith_portal / patient123                   ║"
echo "  ║  Press Ctrl+C to stop                                 ║"
echo "  ║                                                       ║"
echo "  ║  © 2026 Enlightec Ltd.                                ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo ""
cd "${SCRIPT_DIR}"
python3 run_web.py "$PORT"
LAUNCHER
    }

    _desktop_launcher() {
        _launcher_header
        cat <<'LAUNCHER'
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
LAUNCHER
    }

    _cloud_launcher() {
        cat <<'LAUNCHER'
#!/usr/bin/env bash
# MedPharm ERP - Cloud API Server Quick Start
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# License: GNU General Public License v3.0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/venv/bin/activate" 2>/dev/null || true
export PYTHONPATH="${SCRIPT_DIR}"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

if ! python3 -c "import flask_cors" 2>/dev/null; then
    echo "Installing cloud dependencies..."
    pip install -r "${SCRIPT_DIR}/requirements-cloud.txt"
fi

export MEDPHARM_DB_PATH="${SCRIPT_DIR}/data/medpharm.db"
export MEDPHARM_DEBUG=${MEDPHARM_DEBUG:-true}
export MEDPHARM_JWT_SECRET=${MEDPHARM_JWT_SECRET:-dev-secret-do-not-use-in-production}
export MEDPHARM_PORT=${MEDPHARM_PORT:-8080}

echo ""
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║  MedPharm ERP - Cloud API Server                     ║"
echo "  ║  Running at: http://localhost:${MEDPHARM_PORT}                 ║"
echo "  ║  API Base: http://localhost:${MEDPHARM_PORT}/api/v1            ║"
echo "  ║                                                       ║"
echo "  ║  Patient Login: jsmith_portal / patient123            ║"
echo "  ║  Staff Login:   dr.carter / doctor123                 ║"
echo "  ║  Press Ctrl+C to stop                                 ║"
echo "  ║                                                       ║"
echo "  ║  © 2026 Enlightec Ltd.                                ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo ""

cd "${SCRIPT_DIR}"
python3 run_cloud.py
LAUNCHER
    }

    _docs_launcher() {
        _launcher_header
        cat <<'LAUNCHER'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/venv/bin/activate" 2>/dev/null || true
export PYTHONPATH="${SCRIPT_DIR}"
cd "${SCRIPT_DIR}"
python3 docs/generate_pdf.py
LAUNCHER
    }

    _write_launcher_if_missing "${SCRIPT_DIR}/start_web.sh"     _web_launcher
    _write_launcher_if_missing "${SCRIPT_DIR}/start_desktop.sh" _desktop_launcher
    _write_launcher_if_missing "${SCRIPT_DIR}/start_cloud.sh"   _cloud_launcher
    _write_launcher_if_missing "${SCRIPT_DIR}/generate_docs.sh" _docs_launcher
}

# ── Validate Installation ────────────────────────────────────────────────────

validate_install() {
    header "Validating Installation"

    local errors=0

    # Check core imports
    info "Checking database module..."
    "$PYTHON" -c "from database.db_manager import DatabaseManager; print('  OK')" 2>/dev/null \
        && log "Database module: OK" \
        || { warn "Database module: FAILED"; ((errors++)); }

    info "Checking web module..."
    "$PYTHON" -c "from web.app import create_app; print('  OK')" 2>/dev/null \
        && log "Web module: OK" \
        || { warn "Web module: FAILED"; ((errors++)); }

    info "Checking Qt module..."
    "$PYTHON" -c "import PyQt6.QtWidgets; print('  OK')" 2>/dev/null \
        && log "Qt module: OK" \
        || { warn "Qt module: Not available (desktop app requires display + PyQt6)"; }

    info "Checking matplotlib..."
    "$PYTHON" -c "import matplotlib; print('  OK')" 2>/dev/null \
        && log "Matplotlib: OK" \
        || { warn "Matplotlib: Not available (analytics charts disabled)"; }

    info "Checking reportlab..."
    "$PYTHON" -c "import reportlab; print('  OK')" 2>/dev/null \
        && log "ReportLab: OK" \
        || { warn "ReportLab: Not available (PDF generation disabled)"; }

    # Run integration test
    info "Running integration test..."
    PYTHONPATH="${SCRIPT_DIR}" "$PYTHON" -c "
from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from web.app import create_app
import tempfile, os, re

db = os.path.join(tempfile.gettempdir(), 'medpharm_test_install.db')
if os.path.exists(db):
    os.remove(db)
dm = DatabaseManager(db)
dm.init_db()
seed_database(dm)
app = create_app(dm)
c = app.test_client()

# Login flow now requires a CSRF token (HIPAA hardening, 1.6.0+).
login_page = c.get('/login').data.decode()
m = re.search(r'name=\"csrf_token\" value=\"([^\"]+)\"', login_page)
assert m, 'CSRF token not present on /login page'
resp = c.post('/login', data={
    'username': 'jsmith_portal',
    'password': 'patient123',
    'csrf_token': m.group(1),
})
assert resp.status_code in (200, 302), f'login POST failed: {resp.status_code}'

assert c.get('/dashboard').status_code == 200
assert c.get('/prescriptions').status_code == 200
assert c.get('/billing').status_code == 200
assert c.get('/records').status_code == 200
assert c.get('/profile').status_code == 200

stats = dm.get_dashboard_stats()
assert stats['patient_count'] == 15
assert len(dm.get_all_medications()) == 55

os.remove(db)
print('  All integration tests passed')
" 2>/dev/null && log "Integration tests: ALL PASSED" \
    || { warn "Integration tests: Some tests failed (check install.log)"; ((errors++)); }

    if (( errors > 0 )); then
        warn "${errors} issue(s) detected. Check install.log for details."
    else
        log "All validations passed"
    fi
}

# ── Print Summary ─────────────────────────────────────────────────────────────

print_summary() {
    echo -e "\n${GREEN}${BOLD}"
    cat << 'DONE'
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║          ✓ INSTALLATION COMPLETE                              ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
DONE
    echo -e "${NC}"

    echo -e "${BOLD}Quick Start:${NC}\n"
    echo -e "  ${CYAN}1. Activate virtual environment:${NC}"
    echo -e "     source ${VENV_DIR}/bin/activate\n"
    echo -e "  ${CYAN}2. Start the Patient Web Portal:${NC}"
    echo -e "     ./start_web.sh"
    echo -e "     ${DIM}→ http://localhost:5000  (login: jsmith_portal / patient123)${NC}\n"
    echo -e "  ${CYAN}3. Start the Desktop Application:${NC}"
    echo -e "     ./start_desktop.sh"
    echo -e "     ${DIM}→ Login: dr.carter / doctor123${NC}\n"
    echo -e "  ${CYAN}4. Start the Cloud API Server:${NC}"
    echo -e "     ./start_cloud.sh"
    echo -e "     ${DIM}→ http://localhost:8080/api/v1  (for Android/iOS/Windows/macOS clients)${NC}\n"
    echo -e "  ${CYAN}5. Generate PDF Documentation:${NC}"
    echo -e "     ./generate_docs.sh"
    echo -e "     ${DIM}→ Output: docs/MedPharm_ERP_Documentation.pdf${NC}\n"

    echo -e "${BOLD}Default Credentials:${NC}\n"
    echo -e "  ${BOLD}Desktop App (Staff):${NC}"
    echo -e "    Doctor:        dr.carter / doctor123"
    echo -e "    Doctor:        dr.chen / doctor123"
    echo -e "    Psychiatrist:  dr.brooks / doctor123"
    echo -e "    Pharmacist:    pharm.davis / pharm123"
    echo -e "    Admin:         admin / admin123\n"
    echo -e "  ${BOLD}Web Portal (Patients):${NC}"
    echo -e "    John Smith:    jsmith_portal / patient123"
    echo -e "    Maria Johnson: mjohnson_portal / patient123"
    echo -e "    Emily Williams: ewilliams_portal / patient123"
    echo -e "    Sarah Davis:   sdavis_portal / patient123"
    echo -e "    Linda Martinez: lmartinez_portal / patient123\n"

    echo -e "${BOLD}Docker Hub Alternative:${NC}"
    echo -e "  Skip the Python build and pull pre-built images instead:"
    echo -e "    ./install.sh --docker                    ${DIM}# API only (port 8080)${NC}"
    echo -e "    ./install.sh --docker-server             ${DIM}# Full stack (port 80)${NC}"
    echo -e "    ./install.sh --docker --docker-server    ${DIM}# Both at once${NC}"
    echo -e "  Or pull directly:"
    echo -e "    docker pull enlightec/medpharm-api:latest"
    echo -e "    docker pull enlightec/medpharm-server:latest"
    echo -e "  Docker Hub: ${DIM}https://hub.docker.com/u/enlightec${NC}\n"

    echo -e "${DIM}Database: ${DB_PATH}${NC}"
    echo -e "${DIM}Logs:     ${LOG_FILE}${NC}\n"
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
    cd "$SCRIPT_DIR"
    echo "" > "$LOG_FILE"

    banner

    # Docker Hub deployment path — --docker and --docker-server may be set
    # individually or together on the same command line. When both are set,
    # install the API-only container first, then the full-stack container
    # (whose direct API host port is auto-remapped to 8081 inside
    # install_docker_server to avoid clashing with the API-only 8080).
    if [[ "$INSTALL_DOCKER_API" == "true" || "$INSTALL_DOCKER_SERVER" == "true" ]]; then
        check_docker
        if [[ "$INSTALL_DOCKER_API" == "true" ]]; then
            install_docker_api
        fi
        if [[ "$INSTALL_DOCKER_SERVER" == "true" ]]; then
            install_docker_server
        fi
        if [[ "$INSTALL_DOCKER_API" == "true" && "$INSTALL_DOCKER_SERVER" == "true" ]]; then
            echo -e "${BOLD}Combined deployment summary (TLS enabled, self-signed):${NC}"
            echo -e "  API-only:    https://localhost:8080/api/v1   ${DIM}(enlightec/medpharm-api, curl -k)${NC}"
            echo -e "  Full stack:  https://localhost/              ${DIM}(enlightec/medpharm-server via Nginx, curl -k)${NC}"
            echo -e "  Full-stack direct API:    http://localhost:${SERVER_API_PORT:-8081}/ ${DIM}(plain)${NC}"
            echo -e "  Full-stack direct Portal: http://localhost:5000/ ${DIM}(plain)${NC}\n"
        fi
        if [[ "$INSTALL_NGROK" == "true" ]]; then
            install_ngrok
            if [[ "$NGROK_LOGIN" == "true" || ( "$START_NGROK" == "true" && -z "$NGROK_AUTHTOKEN_ARG" ) ]]; then
                ngrok_login_and_capture_token \
                    || warn "Skipping interactive token capture; the tunnel will fail without one."
            fi
            [[ "$START_NGROK" == "true" ]] && start_ngrok_tunnel
        fi
        return
    fi

    if [[ "$INSTALL_NGROK" == "true" && "$INSTALL_DOCKER_API" != "true" && "$INSTALL_DOCKER_SERVER" != "true" ]]; then
        # Standalone --ngrok / --install-ngrok / --ngrok-login path — skip the
        # Python venv work and just provision the tunnel agent (and, when
        # asked, capture the auth token interactively). This covers operators
        # who only need to expose an already-running deployment, plus the
        # token-rotation workflow `./install.sh --ngrok-login`.
        install_ngrok
        if [[ "$NGROK_LOGIN" == "true" || ( "$START_NGROK" == "true" && -z "$NGROK_AUTHTOKEN_ARG" ) ]]; then
            ngrok_login_and_capture_token \
                || warn "Skipping interactive token capture; the tunnel will fail without one."
        fi
        [[ "$START_NGROK" == "true" ]] && start_ngrok_tunnel
        return
    fi

    detect_os
    check_python

    export PYTHONPATH="${SCRIPT_DIR}"

    install_system_deps
    setup_venv
    install_python_deps
    init_database
    create_launchers
    validate_install
    print_summary
}

main "$@"
