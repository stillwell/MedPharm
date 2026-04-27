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
# ║  MedPharm ERP - Source Code Update Checker                                 ║
# ║  Polls GitHub (stillwell/MedPharm) for new commits, optionally backs up    ║
# ║  the local database, then fast-forwards the working tree.                  ║
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
LOG_FILE="${SCRIPT_DIR}/update.log"
LOCK_DIR="${SCRIPT_DIR}/.update.lock.d"

# Pick the SQLite database to back up. Priority order matches the rest of
# MedPharm so the right file gets snapshotted regardless of how the operator
# is running the stack:
#   1. MEDPHARM_DB_PATH env var       — explicit override, always wins
#   2. medpharm_erp.db (project root) — run_cloud.py / run_qt.py default
#   3. data/medpharm_erp.db           — docker-compose volume mount default
#   4. data/medpharm.db               — legacy path the previous version
#                                       hard-coded; kept as a final fallback
# detect_db_path() prints the chosen path or empty when no DB exists yet.
detect_db_path() {
    if [[ -n "${MEDPHARM_DB_PATH:-}" && -f "${MEDPHARM_DB_PATH}" ]]; then
        printf '%s\n' "$MEDPHARM_DB_PATH"
        return
    fi
    for p in \
        "${SCRIPT_DIR}/medpharm_erp.db" \
        "${SCRIPT_DIR}/data/medpharm_erp.db" \
        "${SCRIPT_DIR}/data/medpharm.db"
    do
        if [[ -f "$p" ]]; then
            printf '%s\n' "$p"
            return
        fi
    done
}
DB_PATH="$(detect_db_path)"
DB_DIR="$(dirname "${DB_PATH:-${SCRIPT_DIR}/data/.}")"
BACKUP_DIR="${SCRIPT_DIR}/data/backups"

EXPECTED_REPO_REGEX='github\.com[:/]stillwell/MedPharm(\.git)?/?$'
DEFAULT_REMOTE="origin"

CHECK_ONLY=false
NO_BACKUP=false
ASSUME_YES=false
AUTO=false
BRANCH=""
SCHEDULE_ACTION=""    # install | uninstall | show
SCHEDULE_PERIOD="weekly"   # hourly | daily | weekly | monthly | OnCalendar=...

SCHEDULE_MARKER="# medpharm-auto-update"
SYSTEMD_USER_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SYSTEMD_SERVICE_NAME="medpharm-update.service"
SYSTEMD_TIMER_NAME="medpharm-update.timer"

# ── Parse Arguments ──────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        --check-only|--check)  CHECK_ONLY=true ;;
        --no-backup)           NO_BACKUP=true ;;
        --yes|-y)              ASSUME_YES=true ;;
        --auto)                AUTO=true; ASSUME_YES=true ;;
        --branch=*)            BRANCH="${arg#--branch=}" ;;
        --install-schedule)              SCHEDULE_ACTION=install ;;
        --install-schedule=*)            SCHEDULE_ACTION=install
                                         SCHEDULE_PERIOD="${arg#--install-schedule=}" ;;
        --uninstall-schedule|--remove-schedule) SCHEDULE_ACTION=uninstall ;;
        --show-schedule)                 SCHEDULE_ACTION=show ;;
        --help|-h)
            cat <<HELP
Usage: ./update.sh [OPTIONS]

Checks https://github.com/stillwell/MedPharm for new commits on the tracked
branch, then (optionally) backs up the local SQLite database and fast-forwards
the working tree.

Run-mode options:
  --check-only        Only report whether updates are available; do not pull
  --no-backup         Skip the database backup prompt (NOT recommended)
  --yes, -y           Assume "yes" for backup + update prompts (non-interactive)
  --auto              Fully unattended: implies --yes, suppresses the banner,
                      exits 0 silently when already up to date. Suitable for
                      cron / systemd timers. Database backup STILL runs unless
                      you also pass --no-backup.
  --branch=<ref>      Compare/pull a specific branch (default: current branch)

Schedule-management options (set up an automatic recurring auto-update):
  --install-schedule[=PERIOD]
                      Install a recurring "./update.sh --auto" job. PERIOD is
                      one of: hourly, daily, weekly (default), monthly, or a
                      raw "OnCalendar=..." spec for systemd timers. Prefers a
                      systemd --user timer; falls back to crontab when systemd
                      is unavailable.
  --uninstall-schedule
                      Remove the recurring job (whichever method installed it).
  --show-schedule     Print the installed schedule, if any.

  --help, -h          Show this message

Examples:
  ./update.sh                              # interactive: check, backup DB, pull
  ./update.sh --check-only                 # just report pending commits
  ./update.sh --yes                        # non-interactive update with backup
  ./update.sh --auto                       # silent if up-to-date; meant for cron
  ./update.sh --install-schedule=daily     # install a daily auto-update timer
  ./update.sh --show-schedule              # what will run, and when
  ./update.sh --uninstall-schedule         # remove the recurring job
HELP
            exit 0
            ;;
        *)
            echo -e "${RED}[✗]${NC} Unknown option: $arg" >&2
            echo "    Try: ./update.sh --help" >&2
            exit 2
            ;;
    esac
done

# Auto-non-interactive when stdin is not a TTY (CI, piped input, etc.)
if [[ ! -t 0 ]]; then
    ASSUME_YES=true
fi

# ── Helper Functions ──────────────────────────────────────────────────────────
#
# In --auto mode (cron / systemd timer):
#   - log/info/header/banner are silent on stdout (log file only)
#   - warn writes a single line to the log only (no email noise)
#   - fail still writes to stderr so cron emails on real failures
#   - summary_line() is the explicit stdout signal that something changed
# In interactive mode all of these print to the terminal as before.

_log_only() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$1] ${*:2}" >> "$LOG_FILE"
}

log() {
    _log_only OK "$@"
    [[ "$AUTO" == "true" ]] || echo -e "${GREEN}[✓]${NC} $*"
}
warn() {
    _log_only WARN "$@"
    [[ "$AUTO" == "true" ]] || echo -e "${YELLOW}[!]${NC} $*"
}
fail() {
    _log_only FAIL "$@"
    if [[ "$AUTO" == "true" ]]; then
        echo "medpharm-update: $*" >&2
    else
        echo -e "${RED}[✗]${NC} $*" >&2
    fi
    release_lock
    exit 1
}
info() {
    [[ "$AUTO" == "true" ]] && _log_only INFO "$@" \
        || echo -e "${BLUE}[i]${NC} $*"
}
header() {
    [[ "$AUTO" == "true" ]] && _log_only "──" "$@" \
        || echo -e "\n${CYAN}${BOLD}═══ $* ═══${NC}\n"
}
# Single line emitted to stdout when --auto actually applied an update; this
# is the one place cron will email from on success.
summary_line() {
    if [[ "$AUTO" == "true" ]]; then
        echo "medpharm-update: $*"
    fi
    _log_only SUMMARY "$@"
}

confirm() {
    # confirm "prompt" [default_y]   -> returns 0 on yes, 1 on no
    local prompt="$1" default="${2:-N}" reply
    if [[ "$ASSUME_YES" == "true" ]]; then
        return 0
    fi
    local hint="(y/N)"
    [[ "$default" == "Y" ]] && hint="(Y/n)"
    read -p "    ${prompt} ${hint}: " -n 1 -r reply
    echo
    if [[ -z "$reply" ]]; then
        [[ "$default" == "Y" ]]
        return $?
    fi
    [[ "$reply" =~ ^[Yy]$ ]]
}

banner() {
    [[ "$AUTO" == "true" ]] && return
    echo -e "${CYAN}${BOLD}"
    cat << 'BANNER'
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                                                                          ║
    ║                  MedPharm ERP — Source Update Checker                    ║
    ║              github.com/stillwell/MedPharm  →  local working tree        ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
}

# ── Concurrency lock ──────────────────────────────────────────────────────────
#
# Two simultaneous update.sh runs (e.g. operator + scheduled timer) can leave
# the git index half-updated. Acquire a directory-based lock with a PID
# staleness check so a previous crash does not block forever. In --auto mode
# a busy lock is a silent exit 0 (don't email cron); in interactive mode it
# is a clear refusal.

HOLD_LOCK=0   # only release_lock when this is 1

acquire_lock() {
    if mkdir "$LOCK_DIR" 2>/dev/null; then
        echo "$$" > "$LOCK_DIR/pid"
        HOLD_LOCK=1
        trap 'release_lock' EXIT INT TERM
        return 0
    fi

    local owner_pid
    owner_pid="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
    if [[ -n "$owner_pid" ]] && kill -0 "$owner_pid" 2>/dev/null; then
        # Another live process holds the lock. Do NOT touch it. In --auto we
        # exit 0 silently (cron skips quietly); interactively we explain.
        if [[ "$AUTO" == "true" ]]; then
            _log_only INFO "another update.sh (pid $owner_pid) is running; skipping this auto run"
            exit 0
        fi
        # Bypass the normal fail() so release_lock isn't called for a lock we
        # never owned.
        _log_only FAIL "Another update.sh is already running (pid $owner_pid)"
        echo -e "${RED}[✗]${NC} Another update.sh is already running (pid $owner_pid). Lock: $LOCK_DIR" >&2
        exit 1
    fi

    # Stale lock — previous run died. Steal it.
    rm -rf "$LOCK_DIR"
    mkdir "$LOCK_DIR" || fail "Could not create lock at $LOCK_DIR"
    echo "$$" > "$LOCK_DIR/pid"
    HOLD_LOCK=1
    trap 'release_lock' EXIT INT TERM
    _log_only INFO "stole stale lock from pid $owner_pid"
}

release_lock() {
    [[ "$HOLD_LOCK" -eq 1 ]] || return 0
    HOLD_LOCK=0
    rm -rf "$LOCK_DIR" 2>/dev/null || true
}

# ── Repo Verification ─────────────────────────────────────────────────────────

verify_repo() {
    header "Verifying Repository"

    command -v git >/dev/null 2>&1 || fail "git is not installed"

    git -C "$SCRIPT_DIR" rev-parse --git-dir >/dev/null 2>&1 \
        || fail "${SCRIPT_DIR} is not a git working tree (was MedPharm cloned with git?)"

    local remote_url
    remote_url="$(git -C "$SCRIPT_DIR" remote get-url "$DEFAULT_REMOTE" 2>/dev/null || true)"
    [[ -z "$remote_url" ]] && fail "No '${DEFAULT_REMOTE}' remote configured"

    if [[ ! "$remote_url" =~ $EXPECTED_REPO_REGEX ]]; then
        warn "Remote '${DEFAULT_REMOTE}' is ${remote_url}"
        warn "Expected something matching github.com/stillwell/MedPharm"
        confirm "Continue anyway?" || fail "Aborted by user"
    fi

    log "Remote: ${remote_url}"

    if [[ -z "$BRANCH" ]]; then
        BRANCH="$(git -C "$SCRIPT_DIR" symbolic-ref --short HEAD 2>/dev/null || true)"
        [[ -z "$BRANCH" ]] && fail "HEAD is detached; pass --branch=<name> to choose a branch"
    fi
    log "Branch: ${BRANCH}"
}

# ── Remote Check ──────────────────────────────────────────────────────────────

check_remote() {
    header "Checking for Updates"

    info "Fetching ${DEFAULT_REMOTE}/${BRANCH}..."
    git -C "$SCRIPT_DIR" fetch --quiet "$DEFAULT_REMOTE" "$BRANCH" 2>>"$LOG_FILE" \
        || fail "git fetch failed (see ${LOG_FILE})"

    local local_sha remote_sha base_sha
    local_sha="$(git -C "$SCRIPT_DIR" rev-parse "HEAD")"
    remote_sha="$(git -C "$SCRIPT_DIR" rev-parse "${DEFAULT_REMOTE}/${BRANCH}")"
    base_sha="$(git -C "$SCRIPT_DIR" merge-base "HEAD" "${DEFAULT_REMOTE}/${BRANCH}" 2>/dev/null || echo "")"

    info "Local  HEAD: ${local_sha:0:12}"
    info "Remote HEAD: ${remote_sha:0:12}"

    if [[ "$local_sha" == "$remote_sha" ]]; then
        log "Already up to date — no new commits on ${DEFAULT_REMOTE}/${BRANCH}"
        AHEAD_COUNT=0
        BEHIND_COUNT=0
        return 0
    fi

    if [[ -n "$base_sha" && "$base_sha" == "$local_sha" ]]; then
        # Local is strictly behind — pure fast-forward case
        BEHIND_COUNT="$(git -C "$SCRIPT_DIR" rev-list --count "HEAD..${DEFAULT_REMOTE}/${BRANCH}")"
        AHEAD_COUNT=0
        log "${BEHIND_COUNT} new commit(s) available"
        echo
        git -C "$SCRIPT_DIR" log --oneline --decorate --no-merges \
            "HEAD..${DEFAULT_REMOTE}/${BRANCH}" | sed 's/^/    /'
        echo
    elif [[ -n "$base_sha" && "$base_sha" == "$remote_sha" ]]; then
        # Local is strictly ahead — nothing to pull
        AHEAD_COUNT="$(git -C "$SCRIPT_DIR" rev-list --count "${DEFAULT_REMOTE}/${BRANCH}..HEAD")"
        BEHIND_COUNT=0
        warn "Local branch is ${AHEAD_COUNT} commit(s) ahead of ${DEFAULT_REMOTE}/${BRANCH}"
        warn "Nothing to pull from upstream"
    else
        # Diverged
        AHEAD_COUNT="$(git -C "$SCRIPT_DIR" rev-list --count "${DEFAULT_REMOTE}/${BRANCH}..HEAD")"
        BEHIND_COUNT="$(git -C "$SCRIPT_DIR" rev-list --count "HEAD..${DEFAULT_REMOTE}/${BRANCH}")"
        warn "Branches have diverged: local ahead ${AHEAD_COUNT}, behind ${BEHIND_COUNT}"
        warn "A plain fast-forward will not work; resolve manually with rebase/merge"
    fi
}

# ── Database Backup ───────────────────────────────────────────────────────────

backup_database() {
    header "Database Backup"

    if [[ "$NO_BACKUP" == "true" ]]; then
        warn "Skipping database backup (--no-backup)"
        return 0
    fi

    if [[ ! -f "$DB_PATH" ]]; then
        info "No database found at ${DB_PATH} — nothing to back up"
        return 0
    fi

    local size_human
    size_human="$(du -h "$DB_PATH" | awk '{print $1}')"
    info "Database: ${DB_PATH} (${size_human})"

    if ! confirm "Back up the database before updating?" Y; then
        warn "Skipping database backup at user request"
        return 0
    fi

    mkdir -p "$BACKUP_DIR"
    local stamp
    stamp="$(date '+%Y%m%d-%H%M%S')"
    local target="${BACKUP_DIR}/medpharm-${stamp}.db"

    # Prefer the SQLite .backup command (online, consistent) when sqlite3 is
    # available; fall back to a plain file copy otherwise.
    if command -v sqlite3 >/dev/null 2>&1; then
        info "Using sqlite3 .backup for a consistent online copy..."
        if sqlite3 "$DB_PATH" ".backup '${target}'" 2>>"$LOG_FILE"; then
            log "Backup written: ${target}"
        else
            warn "sqlite3 .backup failed; falling back to file copy"
            cp -p "$DB_PATH" "$target" || fail "Database copy failed"
            log "Backup written (cp): ${target}"
        fi
    else
        cp -p "$DB_PATH" "$target" || fail "Database copy failed"
        log "Backup written (cp): ${target}"
    fi

    # Capture WAL/SHM sidecars too if they exist (only meaningful with cp path)
    [[ -f "${DB_PATH}-wal" ]] && cp -p "${DB_PATH}-wal" "${target}-wal" 2>/dev/null && info "  + WAL sidecar"
    [[ -f "${DB_PATH}-shm" ]] && cp -p "${DB_PATH}-shm" "${target}-shm" 2>/dev/null && info "  + SHM sidecar"

    BACKUP_PATH="$target"
}

# ── Apply Update ──────────────────────────────────────────────────────────────

apply_update() {
    header "Applying Update"

    # Bail early if the working tree is dirty — offer to stash.
    local dirty=""
    if ! git -C "$SCRIPT_DIR" diff --quiet --ignore-submodules HEAD 2>/dev/null; then
        dirty="yes"
    fi
    if [[ -n "$(git -C "$SCRIPT_DIR" ls-files --others --exclude-standard)" ]]; then
        dirty="yes"
    fi

    local stashed="no"
    if [[ -n "$dirty" ]]; then
        # In --auto, refuse rather than auto-stashing. Stashing without an
        # operator watching is a foot-gun: a botched re-apply silently leaves
        # work in 'git stash list', and a scheduled run is the last context in
        # which the operator should hunt for it. Surface the dirty state via
        # stderr so cron emails the owner.
        if [[ "$AUTO" == "true" ]]; then
            warn "Working tree has uncommitted changes:"
            git -C "$SCRIPT_DIR" status --short >> "$LOG_FILE"
            fail "Auto update refuses to touch a dirty tree. Commit / stash and re-run, or run interactively."
        fi
        warn "Working tree has uncommitted changes:"
        git -C "$SCRIPT_DIR" status --short | sed 's/^/      /'
        if confirm "Stash local changes before pulling? (recover with: git stash pop)"; then
            git -C "$SCRIPT_DIR" stash push -u -m "update.sh auto-stash $(date '+%Y-%m-%d %H:%M:%S')" \
                >>"$LOG_FILE" 2>&1 || fail "git stash failed"
            stashed="yes"
            log "Local changes stashed"
        else
            fail "Aborted: working tree must be clean for fast-forward update"
        fi
    fi

    info "Pulling ${DEFAULT_REMOTE}/${BRANCH} (fast-forward only)..."
    if ! git -C "$SCRIPT_DIR" pull --ff-only "$DEFAULT_REMOTE" "$BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
        warn "Fast-forward pull failed"
        if [[ "$stashed" == "yes" ]]; then
            warn "Restoring stashed changes..."
            git -C "$SCRIPT_DIR" stash pop >>"$LOG_FILE" 2>&1 || warn "git stash pop failed; check 'git stash list'"
        fi
        fail "Update aborted; resolve the branch state manually and retry"
    fi
    log "Working tree fast-forwarded to ${DEFAULT_REMOTE}/${BRANCH}"

    if [[ "$stashed" == "yes" ]]; then
        info "Restoring stashed changes..."
        if git -C "$SCRIPT_DIR" stash pop >>"$LOG_FILE" 2>&1; then
            log "Stashed changes reapplied"
        else
            warn "Could not auto-reapply stash; resolve with: git stash list / git stash pop"
        fi
    fi

    NEW_HEAD="$(git -C "$SCRIPT_DIR" rev-parse HEAD)"
}

# ── Post-Update Checks ────────────────────────────────────────────────────────

post_update() {
    header "Post-Update Checks"

    local changed
    changed="$(git -C "$SCRIPT_DIR" diff --name-only "${PREV_HEAD}..HEAD" 2>/dev/null || true)"

    if echo "$changed" | grep -qE '^requirements(-cloud)?\.txt$'; then
        warn "requirements.txt changed in this update"
        if [[ -d "$VENV_DIR" ]] && confirm "Re-install Python dependencies into the venv now?" Y; then
            # shellcheck disable=SC1091
            source "${VENV_DIR}/bin/activate"
            info "Running: pip install -r requirements.txt"
            pip install -q -r "${SCRIPT_DIR}/requirements.txt" 2>&1 | tee -a "$LOG_FILE" \
                | { grep -v "already satisfied" || true; } \
                || warn "pip install reported errors; review ${LOG_FILE}"
            deactivate || true
            log "Python dependencies refreshed"
        else
            info "Skipped pip install — run ./install.sh or 'pip install -r requirements.txt' later"
        fi
    fi

    if echo "$changed" | grep -qE '^database/'; then
        warn "database/ changed — review schema/seed updates manually"
        info "  Changed files:"
        echo "$changed" | grep -E '^database/' | sed 's/^/      /'
    fi

    if echo "$changed" | grep -qE '^install\.sh$'; then
        warn "install.sh itself changed — re-run ./install.sh if you want the new install logic"
    fi
}

# ── Summary ───────────────────────────────────────────────────────────────────

summary() {
    header "Summary"

    if [[ "${BEHIND_COUNT:-0}" -eq 0 ]]; then
        log "No update applied — already at ${DEFAULT_REMOTE}/${BRANCH}"
        return
    fi

    if [[ "$AUTO" == "true" ]]; then
        # One stdout line, suitable for cron to email. Everything else lives
        # in $LOG_FILE for forensic review.
        local backup_part=""
        if [[ -n "${BACKUP_PATH:-}" ]]; then
            backup_part=" backup=${BACKUP_PATH}"
        elif [[ "$NO_BACKUP" == "true" ]]; then
            backup_part=" backup=skipped"
        fi
        summary_line "updated ${BRANCH} ${PREV_HEAD:0:12} → ${NEW_HEAD:0:12} (${BEHIND_COUNT} commits)${backup_part}"
        return
    fi

    echo -e "${BOLD}Updated:${NC}"
    echo -e "  Branch:     ${BRANCH}"
    echo -e "  Old HEAD:   ${PREV_HEAD:0:12}"
    echo -e "  New HEAD:   ${NEW_HEAD:0:12}"
    echo -e "  Commits:    ${BEHIND_COUNT}"
    if [[ -n "${BACKUP_PATH:-}" ]]; then
        echo -e "  DB backup:  ${BACKUP_PATH}"
    elif [[ "$NO_BACKUP" == "true" ]]; then
        echo -e "  DB backup:  ${YELLOW}skipped (--no-backup)${NC}"
    fi
    echo -e "  Log:        ${LOG_FILE}"
    echo
    info "Restart any running MedPharm services (web/qt/api) to pick up the new code."
}

# ── Schedule install / uninstall / show ───────────────────────────────────────
#
# Installs a recurring "./update.sh --auto" job at the user level. Prefers a
# systemd --user timer (sandboxed, persistent across reboots, missed runs
# caught up after wake) and falls back to crontab when systemd-user is not
# available (containers, headless boxes without a user manager, BSDs).
#
# A recognisable marker (SCHEDULE_MARKER) is written into both flavours so
# install / uninstall / show can locate exactly the entry this script created
# and never touch anything else the operator may have in their crontab.

_have_systemd_user() {
    command -v systemctl >/dev/null 2>&1 || return 1
    # is-system-running is the only call that distinguishes "user manager
    # present" from "command exists but no manager". stderr is muted because
    # offline / degraded states still mean the user manager works.
    systemctl --user is-system-running >/dev/null 2>&1 && return 0
    # Some containers say degraded but still run units fine.
    systemctl --user list-units --type=timer >/dev/null 2>&1
}

_period_to_systemd() {
    case "$1" in
        hourly|daily|weekly|monthly) printf '%s' "$1" ;;
        OnCalendar=*)               printf '%s' "${1#OnCalendar=}" ;;
        cron=*)
            fail "cron= expressions are crontab-only — install with crontab fallback or pass an OnCalendar=... spec"
            ;;
        *) fail "Unknown PERIOD '$1' for systemd timer (use hourly|daily|weekly|monthly or OnCalendar=...)" ;;
    esac
}

_period_to_cron() {
    case "$1" in
        hourly)  printf '0 * * * *' ;;
        daily)   printf '0 3 * * *' ;;
        weekly)  printf '0 3 * * 0' ;;
        monthly) printf '0 3 1 * *' ;;
        cron=*)         printf '%s' "${1#cron=}" ;;
        OnCalendar=*)
            fail "OnCalendar= expressions are systemd-only — pass a cron= spec or install on a systemd host"
            ;;
        *) fail "Unknown PERIOD '$1' for crontab (use hourly|daily|weekly|monthly or cron=...)" ;;
    esac
}

_systemd_unit_paths() {
    printf '%s\n%s\n' \
        "${SYSTEMD_USER_DIR}/${SYSTEMD_SERVICE_NAME}" \
        "${SYSTEMD_USER_DIR}/${SYSTEMD_TIMER_NAME}"
}

_install_systemd() {
    local on_calendar="$1"
    mkdir -p "$SYSTEMD_USER_DIR"

    cat > "${SYSTEMD_USER_DIR}/${SYSTEMD_SERVICE_NAME}" <<UNIT
# ${SCHEDULE_MARKER}
[Unit]
Description=MedPharm ERP — automatic source update
Documentation=https://github.com/stillwell/MedPharm
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/update.sh --auto
Nice=15
IOSchedulingClass=idle
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=${SCRIPT_DIR}
PrivateTmp=true
NoNewPrivileges=true
StandardOutput=append:${LOG_FILE}
StandardError=append:${LOG_FILE}
UNIT

    cat > "${SYSTEMD_USER_DIR}/${SYSTEMD_TIMER_NAME}" <<UNIT
# ${SCHEDULE_MARKER}
[Unit]
Description=MedPharm ERP — automatic source update timer
Documentation=https://github.com/stillwell/MedPharm

[Timer]
OnCalendar=${on_calendar}
Persistent=true
RandomizedDelaySec=10min
Unit=${SYSTEMD_SERVICE_NAME}

[Install]
WantedBy=timers.target
UNIT

    systemctl --user daemon-reload >/dev/null 2>&1 \
        || warn "systemctl --user daemon-reload failed; the timer may not appear until you reload"
    systemctl --user enable --now "${SYSTEMD_TIMER_NAME}" >>"$LOG_FILE" 2>&1 \
        || fail "systemctl --user enable --now ${SYSTEMD_TIMER_NAME} failed (see ${LOG_FILE})"

    log "Installed systemd --user timer ${SYSTEMD_TIMER_NAME} (OnCalendar=${on_calendar})"
    info "Inspect with:  systemctl --user list-timers ${SYSTEMD_TIMER_NAME}"
    info "Run now:       systemctl --user start ${SYSTEMD_SERVICE_NAME}"
    info "Logs:          journalctl --user -u ${SYSTEMD_SERVICE_NAME}  (and ${LOG_FILE})"
}

_uninstall_systemd() {
    # Sets REMOVED_ANY=1 in the caller's scope when it actually removed
    # something. Always returns 0 so set -e does not kill the script when
    # nothing was installed.
    local did=0
    if command -v systemctl >/dev/null 2>&1 && \
       systemctl --user list-unit-files 2>/dev/null | grep -q "^${SYSTEMD_TIMER_NAME}"; then
        systemctl --user disable --now "${SYSTEMD_TIMER_NAME}" >>"$LOG_FILE" 2>&1 || true
        did=1
    fi
    while IFS= read -r unit; do
        if [[ -f "$unit" ]] && grep -q "$SCHEDULE_MARKER" "$unit"; then
            rm -f "$unit"
            did=1
        fi
    done < <(_systemd_unit_paths)
    if [[ $did -eq 1 ]]; then
        command -v systemctl >/dev/null 2>&1 && \
            systemctl --user daemon-reload >/dev/null 2>&1 || true
        REMOVED_ANY=1
    fi
    return 0
}

_install_cron() {
    local cron_expr="$1"
    command -v crontab >/dev/null 2>&1 \
        || fail "crontab command not found — install cron, or use a systemd host for --install-schedule"

    # Snapshot first so the operator can roll back to the previous crontab
    # if anything in this rewrite is wrong.
    local snap="${SCRIPT_DIR}/update.log.crontab-bak.$(date '+%Y%m%d-%H%M%S')"
    crontab -l 2>/dev/null > "$snap" || true
    info "Saved crontab snapshot to ${snap}"

    local tmp
    tmp="$(mktemp)"
    crontab -l 2>/dev/null > "$tmp" || true
    {
        echo "${cron_expr} cd ${SCRIPT_DIR} && ./update.sh --auto >>${LOG_FILE} 2>&1  ${SCHEDULE_MARKER}"
    } >> "$tmp"
    crontab "$tmp" || { rm -f "$tmp"; fail "crontab install failed"; }
    rm -f "$tmp"

    log "Installed crontab entry: ${cron_expr} (marker: ${SCHEDULE_MARKER})"
    info "Inspect with:  crontab -l"
    info "Roll back to: ${snap}  (crontab ${snap})"
}

_uninstall_cron() {
    # Same convention as _uninstall_systemd: set REMOVED_ANY=1 on success;
    # always return 0.
    command -v crontab >/dev/null 2>&1 || return 0
    local current
    current="$(crontab -l 2>/dev/null || true)"
    if ! grep -Fq "$SCHEDULE_MARKER" <<<"$current"; then
        return 0
    fi
    local snap="${SCRIPT_DIR}/update.log.crontab-bak.$(date '+%Y%m%d-%H%M%S')"
    echo "$current" > "$snap"
    info "Saved crontab snapshot to ${snap}"
    grep -Fv "$SCHEDULE_MARKER" <<<"$current" | crontab - \
        || fail "crontab uninstall failed; snapshot at ${snap}"
    REMOVED_ANY=1
    return 0
}

install_schedule() {
    header "Installing Auto-Update Schedule"

    # Refuse double-install: check both backends. Operator must uninstall
    # first if they want to change the cadence.
    local already=""
    if [[ -f "${SYSTEMD_USER_DIR}/${SYSTEMD_TIMER_NAME}" ]]; then
        already="systemd timer at ${SYSTEMD_USER_DIR}/${SYSTEMD_TIMER_NAME}"
    elif command -v crontab >/dev/null 2>&1 && crontab -l 2>/dev/null | grep -Fq "$SCHEDULE_MARKER"; then
        already="crontab entry (marker ${SCHEDULE_MARKER})"
    fi
    if [[ -n "$already" ]]; then
        fail "Auto-update schedule already installed: ${already}. Run --uninstall-schedule first to change it."
    fi

    if _have_systemd_user; then
        local oc; oc="$(_period_to_systemd "$SCHEDULE_PERIOD")"
        _install_systemd "$oc"
    else
        local ce; ce="$(_period_to_cron "$SCHEDULE_PERIOD")"
        warn "systemd --user not available; falling back to crontab"
        _install_cron "$ce"
    fi
}

uninstall_schedule() {
    header "Removing Auto-Update Schedule"
    REMOVED_ANY=0
    _uninstall_systemd
    _uninstall_cron
    if [[ "$REMOVED_ANY" -eq 1 ]]; then
        log "Auto-update schedule removed"
    else
        info "No auto-update schedule was installed; nothing to do"
    fi
}

show_schedule() {
    header "Auto-Update Schedule"
    local found=0
    if [[ -f "${SYSTEMD_USER_DIR}/${SYSTEMD_TIMER_NAME}" ]]; then
        found=1
        info "systemd --user timer:"
        sed -n 's/^/    /p' "${SYSTEMD_USER_DIR}/${SYSTEMD_TIMER_NAME}"
        if command -v systemctl >/dev/null 2>&1; then
            echo
            info "Status:"
            systemctl --user list-timers "${SYSTEMD_TIMER_NAME}" --no-pager 2>&1 | sed 's/^/    /' || true
        fi
    fi
    if command -v crontab >/dev/null 2>&1; then
        local hits
        hits="$(crontab -l 2>/dev/null | grep -F "$SCHEDULE_MARKER" || true)"
        if [[ -n "$hits" ]]; then
            found=1
            echo
            info "crontab entry:"
            echo "$hits" | sed 's/^/    /'
        fi
    fi
    if [[ $found -eq 0 ]]; then
        info "No auto-update schedule installed."
        info "Install one with:  ./update.sh --install-schedule[=daily|weekly|...]"
    fi
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
    cd "$SCRIPT_DIR"
    # Truncate log on each run so it remains tractable; rotation is the
    # operator's responsibility (logrotate or similar).
    : > "$LOG_FILE"

    # Schedule-management subcommands short-circuit the update flow. They do
    # not touch the working tree or the database.
    case "$SCHEDULE_ACTION" in
        install)   install_schedule;   exit 0 ;;
        uninstall) uninstall_schedule; exit 0 ;;
        show)      show_schedule;      exit 0 ;;
    esac

    acquire_lock

    banner
    verify_repo
    check_remote

    if [[ "${BEHIND_COUNT:-0}" -eq 0 ]]; then
        summary
        exit 0
    fi

    if [[ "$CHECK_ONLY" == "true" ]]; then
        info "--check-only set; not applying update"
        exit 0
    fi

    if ! confirm "Apply this update now?" Y; then
        info "Update declined; nothing changed"
        exit 0
    fi

    PREV_HEAD="$(git -C "$SCRIPT_DIR" rev-parse HEAD)"
    backup_database
    apply_update
    post_update
    summary
}

main "$@"
