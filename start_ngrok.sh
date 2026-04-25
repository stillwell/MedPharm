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

# ==============================================================================
# MedPharm ERP - ngrok Tunnel Launcher
#
# Exposes the MedPharm REST API to clients sitting behind a firewall, NAT, or
# carrier-grade NAT by punching a TLS tunnel through ngrok's edge network.
# Reads its auth token from one of (in order):
#   1. --authtoken=<TOKEN> on the command line
#   2. NGROK_AUTHTOKEN environment variable
#   3. ~/.config/ngrok/ngrok.yml (already configured by `ngrok config`)
#
# Usage:
#   ./start_ngrok.sh                      # tunnel to https://localhost:8080
#   ./start_ngrok.sh --port=80            # tunnel to a different port
#   ./start_ngrok.sh --target=8081        # alias for --port
#   ./start_ngrok.sh --authtoken=2abc...  # provide token inline
#   ./start_ngrok.sh --region=eu          # us | eu | ap | au | sa | jp | in
#   ./start_ngrok.sh --domain=med.example.ngrok-free.app
#                                         # pin a reserved hostname
#   ./start_ngrok.sh --stop               # tear down a running tunnel
#
# Side effects on success:
#   data/ngrok_public_url.txt     - https://<random>.ngrok-free.app
#   data/ngrok_client_config.json - {"api_base_url": "<url>/api/v1"}
#   data/ngrok_qr.png             - QR code of the URL (if qrencode/qrcode lib
#                                   is available) — scan from the iOS / Android
#                                   client login screens to auto-fill the URL.
#
# Required: ngrok agent on PATH. Install via:
#   ./install.sh --ngrok            (Debian/Ubuntu/macOS, system-wide via apt
#                                    repo or Homebrew tap)
# Or follow https://ngrok.com/download
#
# Companion: docker-compose.hub.yml ships an `ngrok` service profile so the
# tunnel can run alongside the API container — bring it up with
#   NGROK_AUTHTOKEN=<token> docker compose -f docker-compose.hub.yml \
#       --profile ngrok up -d
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/data"
PID_FILE="${DATA_DIR}/ngrok.pid"
LOG_FILE="${DATA_DIR}/ngrok.log"
URL_FILE="${DATA_DIR}/ngrok_public_url.txt"
JSON_FILE="${DATA_DIR}/ngrok_client_config.json"
QR_FILE="${DATA_DIR}/ngrok_qr.png"

PORT=8080
PROTO="http"
REGION=""
DOMAIN=""
AUTHTOKEN="${NGROK_AUTHTOKEN:-}"
DO_STOP=false
NGROK_API_URL="http://127.0.0.1:4040/api/tunnels"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
fail() { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }
info() { echo -e "${CYAN}[i]${NC} $*"; }
hr()   { echo -e "${BOLD}${CYAN}── $* ──${NC}"; }

# ── Argument parsing ─────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        --port=*|--target=*) PORT="${arg#*=}" ;;
        --proto=*) PROTO="${arg#*=}" ;;
        --region=*) REGION="${arg#*=}" ;;
        --domain=*|--hostname=*) DOMAIN="${arg#*=}" ;;
        --authtoken=*|--token=*) AUTHTOKEN="${arg#*=}" ;;
        --stop|--down|--kill) DO_STOP=true ;;
        --help|-h)
            grep '^#' "$0" | sed 's/^# \?//' | sed -n '20,55p'
            exit 0
            ;;
        *) fail "Unknown option: $arg (use --help for usage)" ;;
    esac
done

mkdir -p "$DATA_DIR"

# ── Helpers ──────────────────────────────────────────────────────────────────

have() { command -v "$1" >/dev/null 2>&1; }

assert_ngrok() {
    have ngrok || fail "ngrok agent not found on PATH. Install with: ./install.sh --ngrok  (or https://ngrok.com/download)"
}

stop_running_tunnel() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid="$(cat "$PID_FILE" 2>/dev/null || true)"
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            info "Stopping ngrok tunnel (pid $pid)..."
            kill "$pid" 2>/dev/null || true
            for _ in 1 2 3 4 5; do
                kill -0 "$pid" 2>/dev/null || break
                sleep 0.4
            done
            kill -9 "$pid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
    # Also kill any orphaned ngrok agents started by this script
    pkill -f "ngrok ${PROTO} ${PORT}" 2>/dev/null || true
}

configure_authtoken_if_needed() {
    # Apply the token if one was supplied; ngrok stores it in its own config.
    if [[ -n "$AUTHTOKEN" ]]; then
        info "Configuring ngrok auth token..."
        ngrok config add-authtoken "$AUTHTOKEN" >/dev/null 2>&1 \
            || warn "ngrok config add-authtoken failed (token may be invalid)"
    fi
}

start_ngrok_agent() {
    local args=("$PROTO" "$PORT" "--log=stdout" "--log-format=logfmt")
    [[ -n "$REGION" ]] && args+=("--region=$REGION")
    [[ -n "$DOMAIN" ]] && args+=("--domain=$DOMAIN")

    info "Launching ngrok ${args[*]}"
    nohup ngrok "${args[@]}" >>"$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" >"$PID_FILE"
    log "ngrok agent started (pid $pid). Log: $LOG_FILE"
}

poll_public_url() {
    local url=""
    local attempt
    for attempt in $(seq 1 40); do
        if have curl; then
            url="$(curl -fsS "$NGROK_API_URL" 2>/dev/null \
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
else:
    for t in d.get("tunnels", []):
        pu = t.get("public_url","")
        if pu:
            print(pu); break
' 2>/dev/null || true)"
        fi
        [[ -n "$url" ]] && { echo "$url"; return 0; }
        sleep 0.5
    done
    return 1
}

write_artifacts() {
    local url="$1"
    local api_url="${url%/}/api/v1"

    echo "$url" >"$URL_FILE"
    log "Wrote $URL_FILE"

    cat >"$JSON_FILE" <<JSON
{
  "api_base_url": "$api_url",
  "public_url": "$url",
  "issued_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "tunnel": "ngrok",
  "schema": 1
}
JSON
    log "Wrote $JSON_FILE"

    # Try to draw a QR code: prefer qrencode (apt: qrencode), fall back to
    # the Python qrcode library if it is importable (pulled in by the venv).
    if have qrencode; then
        qrencode -o "$QR_FILE" -s 8 -m 2 "$api_url" \
            && log "Wrote $QR_FILE (QR for: $api_url)"
    elif python3 -c 'import qrcode' >/dev/null 2>&1; then
        python3 - <<PY
import qrcode
img = qrcode.make("$api_url")
img.save("$QR_FILE")
PY
        log "Wrote $QR_FILE (QR for: $api_url)"
    else
        warn "Skipping QR generation — install 'qrencode' (apt) or run inside the venv (which provides the qrcode Python package)"
    fi
}

print_summary() {
    local url="$1"
    local api_url="${url%/}/api/v1"
    echo
    echo -e "${BOLD}${CYAN}"
    cat <<BANNER
    ╔══════════════════════════════════════════════════════════════════╗
    ║  MedPharm ERP — ngrok Tunnel ACTIVE                              ║
    ╚══════════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
    echo -e "  ${BOLD}Public URL:${NC}      $url"
    echo -e "  ${BOLD}Client API base:${NC} $api_url"
    echo -e "  ${BOLD}Local target:${NC}    ${PROTO}://localhost:${PORT}"
    echo -e "  ${BOLD}Inspector UI:${NC}    http://127.0.0.1:4040  ${DIM}(local-only ngrok dashboard)${NC}"
    echo
    echo -e "  ${BOLD}Artifacts:${NC}"
    echo -e "    Public URL    : $URL_FILE"
    echo -e "    Client config : $JSON_FILE"
    if [[ -f "$QR_FILE" ]]; then
        echo -e "    QR code       : $QR_FILE  ${DIM}(scan from iOS/Android Login screen)${NC}"
    fi
    echo
    echo -e "  ${BOLD}Configure clients:${NC}"
    echo -e "    Paste ${BOLD}$api_url${NC} into the Server URL field on:"
    echo -e "      • Android  (LoginActivity → Scan QR or paste)"
    echo -e "      • iOS      (LoginView    → Scan QR or paste)"
    echo -e "      • macOS    (LoginView    → Paste from clipboard)"
    echo -e "      • Windows  (LoginWindow  → Paste from clipboard)"
    echo
    echo -e "  ${DIM}Stop the tunnel: ./start_ngrok.sh --stop${NC}"
    echo
}

# ── Main ─────────────────────────────────────────────────────────────────────

if [[ "$DO_STOP" == "true" ]]; then
    stop_running_tunnel
    log "Stopped"
    exit 0
fi

assert_ngrok
stop_running_tunnel    # ensure no stale agent fights us for port 4040
configure_authtoken_if_needed

hr "Starting tunnel"
start_ngrok_agent

hr "Polling ngrok local API for public URL"
url="$(poll_public_url || true)"
if [[ -z "$url" ]]; then
    warn "Could not determine the public URL within 20 s."
    warn "Check $LOG_FILE for ngrok errors (often: missing/invalid auth token)."
    fail "Tunnel did not come up cleanly"
fi
log "Public URL: $url"

write_artifacts "$url"
print_summary "$url"
