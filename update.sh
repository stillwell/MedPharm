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
DB_DIR="${SCRIPT_DIR}/data"
DB_PATH="${DB_DIR}/medpharm.db"
BACKUP_DIR="${DB_DIR}/backups"
VENV_DIR="${SCRIPT_DIR}/venv"
LOG_FILE="${SCRIPT_DIR}/update.log"

EXPECTED_REPO_REGEX='github\.com[:/]stillwell/MedPharm(\.git)?/?$'
DEFAULT_REMOTE="origin"

CHECK_ONLY=false
NO_BACKUP=false
ASSUME_YES=false
BRANCH=""

# ── Parse Arguments ──────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        --check-only|--check)  CHECK_ONLY=true ;;
        --no-backup)           NO_BACKUP=true ;;
        --yes|-y)              ASSUME_YES=true ;;
        --branch=*)            BRANCH="${arg#--branch=}" ;;
        --help|-h)
            cat <<HELP
Usage: ./update.sh [OPTIONS]

Checks https://github.com/stillwell/MedPharm for new commits on the tracked
branch, then (optionally) backs up the local SQLite database and fast-forwards
the working tree.

Options:
  --check-only        Only report whether updates are available; do not pull
  --no-backup         Skip the database backup prompt (NOT recommended)
  --yes, -y           Assume "yes" for backup + update prompts (non-interactive)
  --branch=<ref>      Compare/pull a specific branch (default: current branch)
  --help, -h          Show this message

Examples:
  ./update.sh                    # interactive: check, backup DB, pull
  ./update.sh --check-only       # just report pending commits
  ./update.sh --yes              # non-interactive update with backup
  ./update.sh --branch=master    # force-track master regardless of HEAD
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

log()    { echo -e "${GREEN}[✓]${NC} $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] [OK] $*" >> "$LOG_FILE"; }
warn()   { echo -e "${YELLOW}[!]${NC} $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $*" >> "$LOG_FILE"; }
fail()   { echo -e "${RED}[✗]${NC} $*"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] [FAIL] $*" >> "$LOG_FILE"; exit 1; }
info()   { echo -e "${BLUE}[i]${NC} $*"; }
header() { echo -e "\n${CYAN}${BOLD}═══ $* ═══${NC}\n"; }

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

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
    cd "$SCRIPT_DIR"
    : > "$LOG_FILE"

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
