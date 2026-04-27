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
# ║  MedPharm ERP — System-Service Installer                                    ║
# ║                                                                              ║
# ║  Migrates the MedPharm tree to /opt/medpharm, creates the medpharm system   ║
# ║  user, builds a venv, and installs systemd units for the REST API and the   ║
# ║  patient web portal so they start on boot and restart on failure.           ║
# ║                                                                              ║
# ║  Usage:                                                                      ║
# ║    sudo ./install-services.sh install                                        ║
# ║    sudo ./install-services.sh status                                         ║
# ║    sudo ./install-services.sh logs                                           ║
# ║    sudo ./install-services.sh restart                                        ║
# ║    sudo ./install-services.sh uninstall                                      ║
# ║    ./install-services.sh --help                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_USER="medpharm"
SERVICE_GROUP="medpharm"
NO_CREATE_USER=false
INSTALL_DIR="/opt/medpharm"
API_PORT=8080
WEB_PORT=5000
WORKERS=4
WHICH=both        # api | web | both
SOURCE_MODE=current   # current | clone
NO_START=false
FORCE=false
USER_MODE=false   # true → install as `systemctl --user` units (no sudo)
UPSTREAM_REMOTE="https://github.com/stillwell/MedPharm.git"

SYSTEMD_SYSTEM_DIR="/etc/systemd/system"
SYSTEMD_USER_DIR="${XDG_CONFIG_HOME:-${HOME:-/root}/.config}/systemd/user"

API_TEMPLATE="${SCRIPT_DIR}/systemd/medpharm-api.service.template"
WEB_TEMPLATE="${SCRIPT_DIR}/systemd/medpharm-web.service.template"

# ── Colors / output ───────────────────────────────────────────────────────────
# ANSI-C quoting ($'...') so the variables hold real escape characters; this
# lets the same vars work inside echo -e AND inside `cat <<HEREDOC` blocks.
RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'; CYAN=$'\033[0;36m'; BOLD=$'\033[1m'; DIM=$'\033[2m'; NC=$'\033[0m'

log()    { printf '%s[✓]%s %s\n' "$GREEN"  "$NC" "$*"; }
warn()   { printf '%s[!]%s %s\n' "$YELLOW" "$NC" "$*" >&2; }
fail()   { printf '%s[✗]%s %s\n' "$RED"    "$NC" "$*" >&2; exit 1; }
info()   { printf '%s[i]%s %s\n' "$BLUE"   "$NC" "$*"; }
header() { printf '\n%s%s═══ %s ═══%s\n\n' "$CYAN" "$BOLD" "$*" "$NC"; }

# ── Help ──────────────────────────────────────────────────────────────────────
print_help() {
    cat <<HELP
${BOLD}MedPharm ERP — System-Service Installer${NC}

Migrates the MedPharm source tree to ${BOLD}/opt/medpharm${NC}, creates the
${BOLD}medpharm${NC} system user, builds a Python venv, and installs systemd
units that run the REST API (port ${API_PORT}) and the patient web portal
(port ${WEB_PORT}).

${BOLD}Usage:${NC}
  sudo ./install-services.sh ${CYAN}install${NC}      [OPTIONS]
  sudo ./install-services.sh ${CYAN}uninstall${NC}    [--purge]
  sudo ./install-services.sh ${CYAN}start${NC}        [--api-only|--web-only]
  sudo ./install-services.sh ${CYAN}stop${NC}         [--api-only|--web-only]
  sudo ./install-services.sh ${CYAN}restart${NC}      [--api-only|--web-only]
  sudo ./install-services.sh ${CYAN}status${NC}
  sudo ./install-services.sh ${CYAN}logs${NC}         [--api-only|--web-only] [--follow]
  sudo ./install-services.sh ${CYAN}update-units${NC} (re-render templates only)

${BOLD}Install options:${NC}
  --user=NAME        Service user (default: ${SERVICE_USER})
  --no-create-user   Don't create the user; assume it already exists
  --prefix=PATH      Install dir (default: ${INSTALL_DIR})
  --api-port=N       API listen port (default: ${API_PORT})
  --web-port=N       Web portal listen port (default: ${WEB_PORT})
  --workers=N        gunicorn worker count (default: ${WORKERS})
  --api-only         Install only the API service
  --web-only         Install only the web service
  --from-current     ${DIM}(default)${NC} rsync from this checkout into PREFIX
  --clone-fresh      git clone from ${UPSTREAM_REMOTE} into PREFIX instead
  --no-start         Install + enable but don't start (for staged rollouts)
  --force            Overwrite an existing PREFIX (the existing tree is
                     archived to PREFIX.bak.<timestamp> first)
  --user-mode        Install as systemd --user units (no sudo, no boot
                     start unless 'loginctl enable-linger' is set)

${BOLD}Uninstall options:${NC}
  --purge            Also remove PREFIX and the medpharm user (DESTRUCTIVE).
                     The DB at \${PREFIX}/medpharm_erp.db is archived to
                     /var/backups/medpharm/ first.

${BOLD}Examples:${NC}
  sudo ./install-services.sh install
  sudo ./install-services.sh install --api-only --workers=8
  sudo ./install-services.sh install --user=apphost --no-create-user
  sudo ./install-services.sh status
  sudo ./install-services.sh logs --follow
  sudo ./install-services.sh uninstall --purge

${BOLD}Once running:${NC}  systemctl status medpharm-api medpharm-web
${BOLD}Live logs:${NC}     journalctl -u medpharm-api -u medpharm-web -f

${DIM}Read the unit templates at systemd/medpharm-{api,web}.service.template
to see exactly what gets installed.${NC}
HELP
}

# ── Argument parsing ──────────────────────────────────────────────────────────
ACTION=""
PURGE=false
FOLLOW=false

if [[ $# -eq 0 ]]; then print_help; exit 0; fi

# First positional = subcommand
case "${1:-}" in
    install|uninstall|start|stop|restart|status|logs|update-units) ACTION="$1"; shift ;;
    --help|-h|help|"") print_help; exit 0 ;;
    *) fail "Unknown subcommand: $1 (try --help)" ;;
esac

for arg in "$@"; do
    case "$arg" in
        --user=*)          SERVICE_USER="${arg#--user=}"; SERVICE_GROUP="$SERVICE_USER" ;;
        --no-create-user)  NO_CREATE_USER=true ;;
        --prefix=*)        INSTALL_DIR="${arg#--prefix=}" ;;
        --api-port=*)      API_PORT="${arg#--api-port=}" ;;
        --web-port=*)      WEB_PORT="${arg#--web-port=}" ;;
        --workers=*)       WORKERS="${arg#--workers=}" ;;
        --api-only)        WHICH=api ;;
        --web-only)        WHICH=web ;;
        --from-current)    SOURCE_MODE=current ;;
        --clone-fresh)     SOURCE_MODE=clone ;;
        --no-start)        NO_START=true ;;
        --force)           FORCE=true ;;
        --user-mode)       USER_MODE=true ;;
        --purge)           PURGE=true ;;
        --follow|-f)       FOLLOW=true ;;
        --help|-h)         print_help; exit 0 ;;
        *) fail "Unknown option: $arg (try --help)" ;;
    esac
done

# ── Sudo / mode handling ──────────────────────────────────────────────────────
require_sudo() {
    if [[ "$USER_MODE" == "true" ]]; then return 0; fi
    if [[ "$EUID" -ne 0 ]]; then
        fail "$ACTION requires root (re-run with sudo) or pass --user-mode for a no-sudo install"
    fi
}

systemctl_cmd() {
    if [[ "$USER_MODE" == "true" ]]; then
        systemctl --user "$@"
    else
        systemctl "$@"
    fi
}

units_dir() {
    if [[ "$USER_MODE" == "true" ]]; then
        echo "$SYSTEMD_USER_DIR"
    else
        echo "$SYSTEMD_SYSTEM_DIR"
    fi
}

# Names of the units we manage (filtered by --api-only / --web-only).
selected_unit_names() {
    case "$WHICH" in
        api)  echo "medpharm-api.service" ;;
        web)  echo "medpharm-web.service" ;;
        both) echo "medpharm-api.service medpharm-web.service" ;;
    esac
}

# ── Pre-flight checks ─────────────────────────────────────────────────────────
preflight_install() {
    [[ -f "$API_TEMPLATE" ]] || fail "Missing template: $API_TEMPLATE"
    [[ -f "$WEB_TEMPLATE" ]] || fail "Missing template: $WEB_TEMPLATE"
    command -v systemctl >/dev/null 2>&1 || fail "systemctl not found — system services require systemd"
    command -v rsync >/dev/null 2>&1 || command -v cp >/dev/null 2>&1 \
        || fail "Neither rsync nor cp available; cannot relocate the source tree"
    command -v python3 >/dev/null 2>&1 || fail "python3 not found"
}

# ── User management ───────────────────────────────────────────────────────────
ensure_user() {
    if [[ "$USER_MODE" == "true" ]]; then return 0; fi
    if id "$SERVICE_USER" >/dev/null 2>&1; then
        info "Service user '${SERVICE_USER}' already exists (uid=$(id -u "$SERVICE_USER"))"
        return 0
    fi
    if [[ "$NO_CREATE_USER" == "true" ]]; then
        fail "User '${SERVICE_USER}' does not exist and --no-create-user was set"
    fi
    info "Creating system user '${SERVICE_USER}' (no login shell, home ${INSTALL_DIR})"
    # -r system user, -s nologin, -d /opt/medpharm, -M don't create home
    # (we manage that directory separately).
    if ! useradd --system --shell /usr/sbin/nologin --home-dir "$INSTALL_DIR" \
                 --no-create-home --user-group "$SERVICE_USER" 2>/dev/null; then
        # useradd long-options are not portable across all distros (busybox,
        # alpine) — fall back to the short forms.
        useradd -r -s /usr/sbin/nologin -d "$INSTALL_DIR" -M -U "$SERVICE_USER" \
            || fail "useradd failed for ${SERVICE_USER}"
    fi
    log "Created user ${SERVICE_USER} (uid=$(id -u "$SERVICE_USER"))"
}

# ── Tree relocation ───────────────────────────────────────────────────────────
sync_tree() {
    if [[ -e "$INSTALL_DIR" && "$FORCE" != "true" ]]; then
        if [[ -d "$INSTALL_DIR/.git" ]]; then
            info "Existing checkout at ${INSTALL_DIR} (skipping migration; pass --force to overwrite)"
            return 0
        fi
        fail "${INSTALL_DIR} exists but is not a git checkout. Use --force to overwrite (the existing tree is archived first)."
    fi

    if [[ -e "$INSTALL_DIR" ]]; then
        local stamp; stamp="$(date '+%Y%m%d-%H%M%S')"
        local archive="${INSTALL_DIR}.bak.${stamp}"
        info "Archiving existing ${INSTALL_DIR} → ${archive}"
        mv "$INSTALL_DIR" "$archive"
    fi

    mkdir -p "$INSTALL_DIR"

    case "$SOURCE_MODE" in
        clone)
            command -v git >/dev/null 2>&1 || fail "git not installed; cannot --clone-fresh"
            info "Cloning ${UPSTREAM_REMOTE} → ${INSTALL_DIR}"
            git clone --depth 50 "$UPSTREAM_REMOTE" "$INSTALL_DIR" \
                || fail "git clone failed"
            ;;
        current)
            info "Migrating current checkout (${SCRIPT_DIR}) → ${INSTALL_DIR}"
            if command -v rsync >/dev/null 2>&1; then
                # Preserve .git so update.sh can fast-forward, but exclude
                # build/dev artifacts and operator-private files.
                rsync -a --delete \
                    --exclude='venv/' \
                    --exclude='.venv/' \
                    --exclude='__pycache__/' \
                    --exclude='*.pyc' --exclude='*.pyo' \
                    --exclude='node_modules/' \
                    --exclude='*.tmp' --exclude='*.lock' \
                    --exclude='.update.lock.d/' \
                    --exclude='data/ngrok.log' \
                    --exclude='data/ngrok.pid' \
                    --exclude='data/backups/' \
                    --exclude='install.log' \
                    --exclude='/medpharm-pdf-venv/' \
                    "${SCRIPT_DIR}/" "${INSTALL_DIR}/" \
                    || fail "rsync failed"
            else
                cp -a "${SCRIPT_DIR}/." "${INSTALL_DIR}/" || fail "cp failed"
            fi
            ;;
    esac

    log "Tree placed at ${INSTALL_DIR}"
}

# ── venv ──────────────────────────────────────────────────────────────────────
build_venv() {
    info "Building Python venv at ${INSTALL_DIR}/venv"
    python3 -m venv "${INSTALL_DIR}/venv" || fail "python3 -m venv failed"
    "${INSTALL_DIR}/venv/bin/pip" install --quiet --upgrade pip wheel \
        || warn "pip upgrade reported errors; continuing"
    "${INSTALL_DIR}/venv/bin/pip" install --quiet -r "${INSTALL_DIR}/requirements-cloud.txt" \
        || fail "pip install -r requirements-cloud.txt failed"
    # The web portal pulls in the same Flask stack but historically lived in
    # requirements.txt; install if present.
    if [[ -f "${INSTALL_DIR}/requirements.txt" ]] && [[ "$WHICH" != "api" ]]; then
        "${INSTALL_DIR}/venv/bin/pip" install --quiet -r "${INSTALL_DIR}/requirements.txt" \
            2>/dev/null || warn "pip install -r requirements.txt reported errors (PyQt6 is desktop-only and is allowed to fail here)"
    fi
    # Make sure gunicorn is present even when only the web target is selected.
    "${INSTALL_DIR}/venv/bin/python" -c 'import gunicorn' 2>/dev/null \
        || "${INSTALL_DIR}/venv/bin/pip" install --quiet gunicorn \
        || fail "Could not install gunicorn"
    log "venv ready"
}

# ── Permissions / runtime dirs ────────────────────────────────────────────────
fix_permissions() {
    mkdir -p "${INSTALL_DIR}/data" "${INSTALL_DIR}/logs"
    if [[ "$USER_MODE" == "true" ]]; then
        # In user mode the invoking user owns the tree already; nothing to do.
        log "Permissions: skipped (user-mode install runs as $(id -un))"
        return 0
    fi
    chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "$INSTALL_DIR"
    # The DB (and its WAL/SHM sidecars) need write access from the service
    # user; everything else can stay owned but read-only-by-policy via
    # systemd's ProtectSystem=strict + ReadWritePaths.
    chmod 750 "$INSTALL_DIR"
    chmod 770 "${INSTALL_DIR}/data" "${INSTALL_DIR}/logs"
    log "Permissions set (owner=${SERVICE_USER}:${SERVICE_GROUP})"
}

# ── Unit rendering / install ──────────────────────────────────────────────────
render_unit() {
    local template="$1" outpath="$2"
    sed \
        -e "s|{{INSTALL_DIR}}|${INSTALL_DIR}|g" \
        -e "s|{{SERVICE_USER}}|${SERVICE_USER}|g" \
        -e "s|{{SERVICE_GROUP}}|${SERVICE_GROUP}|g" \
        -e "s|{{API_PORT}}|${API_PORT}|g" \
        -e "s|{{WEB_PORT}}|${WEB_PORT}|g" \
        -e "s|{{WORKERS}}|${WORKERS}|g" \
        "$template" > "$outpath"

    # User-service adjustments (systemctl --user). The templates are
    # written for the production system-mode posture; for user-mode we
    # have to relax three classes of directives that the user manager
    # cannot satisfy:
    #
    #   1. User= / Group= — illegal in user units (the user manager
    #      already runs as the invoking user). Produces status=217/USER.
    #   2. WantedBy=multi-user.target — multi-user.target is a system
    #      target; user units belong on default.target. Symlink
    #      installation still succeeds but the unit never auto-starts
    #      on session start.
    #   3. The "drop capabilities" hardening block (RestrictSUIDSGID,
    #      LockPersonality, MemoryDenyWriteExecute, RestrictRealtime,
    #      kernel-level Protect*, SystemCall*) needs privileges the
    #      user manager doesn't have, so the unit fails at start time
    #      with status=218/CAPABILITIES.
    #
    # These are stripped only for user-mode; system-mode keeps the full
    # hardening posture.
    if [[ "$USER_MODE" == "true" ]]; then
        sed -i \
            -e '/^User=/d' \
            -e '/^Group=/d' \
            -e 's|^WantedBy=multi-user\.target$|WantedBy=default.target|' \
            -e '/^ProtectKernelTunables=/d' \
            -e '/^ProtectKernelModules=/d' \
            -e '/^ProtectKernelLogs=/d' \
            -e '/^ProtectControlGroups=/d' \
            -e '/^ProtectClock=/d' \
            -e '/^ProtectHostname=/d' \
            -e '/^PrivateDevices=/d' \
            -e '/^RestrictNamespaces=/d' \
            -e '/^RestrictRealtime=/d' \
            -e '/^RestrictSUIDSGID=/d' \
            -e '/^LockPersonality=/d' \
            -e '/^MemoryDenyWriteExecute=/d' \
            -e '/^SystemCallArchitectures=/d' \
            -e '/^SystemCallFilter=/d' \
            -e '/^SystemCallErrorNumber=/d' \
            "$outpath"
    fi

    chmod 644 "$outpath"
}

install_units() {
    local dir; dir="$(units_dir)"
    mkdir -p "$dir"
    if [[ "$WHICH" == "api" || "$WHICH" == "both" ]]; then
        render_unit "$API_TEMPLATE" "${dir}/medpharm-api.service"
        log "Installed ${dir}/medpharm-api.service"
    fi
    if [[ "$WHICH" == "web" || "$WHICH" == "both" ]]; then
        render_unit "$WEB_TEMPLATE" "${dir}/medpharm-web.service"
        log "Installed ${dir}/medpharm-web.service"
    fi
    info "Reloading systemd"
    systemctl_cmd daemon-reload
}

enable_units() {
    for unit in $(selected_unit_names); do
        info "Enabling ${unit}"
        systemctl_cmd enable "$unit" 2>&1 | sed 's/^/    /' || warn "enable ${unit} failed"
    done
}

start_units() {
    for unit in $(selected_unit_names); do
        info "Starting ${unit}"
        systemctl_cmd start "$unit" 2>&1 | sed 's/^/    /' \
            || warn "start ${unit} failed (check: journalctl -u ${unit})"
    done
}

stop_units() {
    for unit in $(selected_unit_names); do
        info "Stopping ${unit}"
        systemctl_cmd stop "$unit" 2>&1 | sed 's/^/    /' || true
    done
}

restart_units() {
    for unit in $(selected_unit_names); do
        info "Restarting ${unit}"
        systemctl_cmd restart "$unit" 2>&1 | sed 's/^/    /' \
            || warn "restart ${unit} failed (check: journalctl -u ${unit})"
    done
}

disable_units() {
    for unit in $(selected_unit_names); do
        systemctl_cmd disable "$unit" 2>&1 | sed 's/^/    /' || true
    done
}

remove_unit_files() {
    local dir; dir="$(units_dir)"
    rm -f "${dir}/medpharm-api.service" "${dir}/medpharm-web.service"
    systemctl_cmd daemon-reload || true
    log "Removed unit files from ${dir}"
}

# ── Subcommand dispatchers ────────────────────────────────────────────────────
do_install() {
    require_sudo
    preflight_install
    header "MedPharm — System Service Install"
    ensure_user
    sync_tree
    build_venv
    fix_permissions
    install_units
    enable_units
    if [[ "$NO_START" == "true" ]]; then
        info "--no-start: services enabled but not started"
    else
        start_units
        sleep 1
        do_status
    fi
    cat <<DONE

${GREEN}${BOLD}Install complete.${NC}

  Install dir : ${INSTALL_DIR}
  Service user: ${SERVICE_USER}
  API         : http://localhost:${API_PORT}/api/v1/health
  Web portal  : http://localhost:${WEB_PORT}/

  Live logs   : journalctl -u medpharm-api -u medpharm-web -f
  Status      : systemctl status medpharm-api medpharm-web
  Config      : drop overrides at /etc/medpharm/medpharm.env (see template
                env vars in systemd/medpharm-*.service.template)
  Auto-update : ${INSTALL_DIR}/update.sh --install-schedule=daily
DONE
}

do_uninstall() {
    require_sudo
    header "MedPharm — Uninstall System Services"
    stop_units
    disable_units
    remove_unit_files
    if [[ "$PURGE" == "true" ]]; then
        if [[ -f "${INSTALL_DIR}/medpharm_erp.db" ]]; then
            local stamp; stamp="$(date '+%Y%m%d-%H%M%S')"
            local archive_dir="/var/backups/medpharm"
            mkdir -p "$archive_dir"
            cp -p "${INSTALL_DIR}/medpharm_erp.db" "${archive_dir}/medpharm_erp-${stamp}.db" \
                || warn "Database archive copy failed"
            log "Database archived to ${archive_dir}/medpharm_erp-${stamp}.db"
        fi
        if [[ -d "$INSTALL_DIR" ]]; then
            rm -rf "$INSTALL_DIR" && log "Removed ${INSTALL_DIR}"
        fi
        if id "$SERVICE_USER" >/dev/null 2>&1; then
            userdel "$SERVICE_USER" 2>/dev/null && log "Removed user ${SERVICE_USER}" \
                || warn "userdel ${SERVICE_USER} failed (still has running processes?)"
        fi
    else
        info "Source tree preserved at ${INSTALL_DIR}; pass --purge to also remove it and the user"
    fi
    log "Uninstall complete"
}

do_status() {
    header "MedPharm — Service Status"
    for unit in $(selected_unit_names); do
        echo -e "${BOLD}── ${unit} ──${NC}"
        systemctl_cmd --no-pager --lines=0 status "$unit" 2>&1 | sed 's/^/  /' || true
        echo
    done
}

do_logs() {
    local args=()
    if [[ "$USER_MODE" == "true" ]]; then args+=("--user"); fi
    for unit in $(selected_unit_names); do
        args+=(-u "$unit")
    done
    if [[ "$FOLLOW" == "true" ]]; then
        info "Tailing logs (Ctrl-C to stop)"
        journalctl "${args[@]}" -f
    else
        journalctl "${args[@]}" --no-pager --since='1 hour ago'
    fi
}

do_update_units() {
    require_sudo
    header "MedPharm — Re-render Units"
    [[ -d "$INSTALL_DIR" ]] || fail "${INSTALL_DIR} does not exist; run install first"
    install_units
    info "Re-rendered. Restart services to pick up changes:"
    info "    systemctl restart medpharm-api medpharm-web"
}

# ── Main ──────────────────────────────────────────────────────────────────────
case "$ACTION" in
    install)      do_install ;;
    uninstall)    do_uninstall ;;
    start)        require_sudo; start_units ;;
    stop)         require_sudo; stop_units ;;
    restart)      require_sudo; restart_units ;;
    status)       do_status ;;
    logs)         do_logs ;;
    update-units) do_update_units ;;
    *)            fail "Unknown subcommand: $ACTION" ;;
esac
