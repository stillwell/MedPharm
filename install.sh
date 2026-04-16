#!/usr/bin/env bash
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
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

# ── Parse Arguments ──────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        --fresh) FRESH=true ;;
        --help|-h)
            echo "Usage: ./install.sh [--fresh]"
            echo "  --fresh   Recreate virtual environment and reinitialize database without prompting"
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
    ╔═════════════════════════════════════════════════════════════════════╗
    ║                                                                     ║
    ║   ███╗   ███╗███████╗██████╗ ██████╗ ██╗  ██╗ █████╗ ██████╗ ███╗  ║
    ║   ████╗ ████║██╔════╝██╔══██╗██╔══██╗██║  ██║██╔══██╗██╔══██╗████║ ║
    ║   ██╔████╔██║█████╗  ██║  ██║██████╔╝███████║███████║██████╔╝██╔═╝ ║
    ║   ██║╚██╔╝██║██╔══╝  ██║  ██║██╔═══╝ ██╔══██║██╔══██║██╔══██╗     ║
    ║   ██║ ╚═╝ ██║███████╗██████╔╝██║     ██║  ██║██║  ██║██║  ██║     ║
    ║   ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ║
    ║                     E R P   S Y S T E M                             ║
    ║           Medical & Pharmaceutical Management v1.0                  ║
    ║                                                                     ║
    ╚═════════════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
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

    # Web portal launcher
    cat > "${SCRIPT_DIR}/start_web.sh" << 'LAUNCHER'
#!/usr/bin/env bash
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
echo "  ╚═══════════════════════════════════════════════════════╝"
echo ""
cd "${SCRIPT_DIR}"
python3 run_web.py "$PORT"
LAUNCHER
    chmod +x "${SCRIPT_DIR}/start_web.sh"
    log "Created start_web.sh"

    # Qt desktop launcher
    cat > "${SCRIPT_DIR}/start_desktop.sh" << 'LAUNCHER'
#!/usr/bin/env bash
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
echo "  ╚═══════════════════════════════════════════════════════╝"
echo ""
cd "${SCRIPT_DIR}"
python3 run_qt.py
LAUNCHER
    chmod +x "${SCRIPT_DIR}/start_desktop.sh"
    log "Created start_desktop.sh"

    # Cloud API server launcher
    cat > "${SCRIPT_DIR}/start_cloud.sh" << 'LAUNCHER'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/venv/bin/activate" 2>/dev/null || true
export PYTHONPATH="${SCRIPT_DIR}"
export MEDPHARM_DEBUG=${MEDPHARM_DEBUG:-true}
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
echo "  ╚═══════════════════════════════════════════════════════╝"
echo ""
cd "${SCRIPT_DIR}"
python3 run_cloud.py
LAUNCHER
    chmod +x "${SCRIPT_DIR}/start_cloud.sh"
    log "Created start_cloud.sh"

    # PDF documentation generator
    cat > "${SCRIPT_DIR}/generate_docs.sh" << 'LAUNCHER'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/venv/bin/activate" 2>/dev/null || true
export PYTHONPATH="${SCRIPT_DIR}"
cd "${SCRIPT_DIR}"
python3 docs/generate_pdf.py
LAUNCHER
    chmod +x "${SCRIPT_DIR}/generate_docs.sh"
    log "Created generate_docs.sh"
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
import tempfile, os

db = os.path.join(tempfile.gettempdir(), 'medpharm_test_install.db')
dm = DatabaseManager(db)
dm.init_db()
seed_database(dm)
app = create_app(dm)
c = app.test_client()

c.post('/login', data={'username':'jsmith_portal','password':'patient123'})
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

    echo -e "${DIM}Database: ${DB_PATH}${NC}"
    echo -e "${DIM}Logs:     ${LOG_FILE}${NC}\n"
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
    cd "$SCRIPT_DIR"
    echo "" > "$LOG_FILE"

    banner
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
