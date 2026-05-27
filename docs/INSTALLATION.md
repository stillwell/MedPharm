# MedPharm ERP — Installation Guide

This document provides in-depth installation instructions for every MedPharm component on every supported host platform. For a high-level overview see the top-level [README](../README.md); for building client binaries from source see [COMPILATION.md](COMPILATION.md).

---

## Table of Contents

1. [Deployment Matrix](#deployment-matrix)
2. [Prerequisites](#prerequisites)
3. [Python Server Installation](#python-server-installation)
   - [Linux (Ubuntu / Debian / Fedora / Arch)](#linux)
   - [macOS](#macos)
   - [Windows (WSL 2)](#windows-wsl-2)
   - [Windows (native)](#windows-native)
4. [Docker Installation](#docker-installation)
5. [Database Initialization & Seeding](#database-initialization--seeding)
6. [Client Runtime Installation](#client-runtime-installation)
7. [Post-Installation Verification](#post-installation-verification)
8. [Uninstallation](#uninstallation)
9. [Troubleshooting](#troubleshooting)

---

## Deployment Matrix

| Component | Host OS | Runtime | Install Method |
|-----------|---------|---------|----------------|
| Cloud REST API | Linux, macOS, Windows, Docker, Kubernetes | Python 3.10+ / Gunicorn | `pip`, `enlightec/medpharm-api`, or `kubectl apply -k k8s/` |
| Web Portal | Linux, macOS, Windows, Docker, Kubernetes | Python 3.10+ / Flask | `pip`, `enlightec/medpharm-server`, or `kubectl apply -k k8s/` |
| Qt Desktop App | Linux (X11/Wayland), macOS, Windows | Python 3.10+ / PyQt6 | `pip` |
| Android Client | Android 8.0+ (API 26) | ART / Kotlin | APK install |
| iOS Client | iOS 16+ | Swift runtime | TestFlight / Xcode |
| macOS Client | macOS 13 Ventura+ | Swift runtime | `.app` bundle / Xcode |
| Windows Client | Windows 10 1809+ | .NET 8 Desktop Runtime | MSI / `dotnet run` |

---

## Prerequisites

### Hardware (minimum)

| Resource | Server | Desktop client |
|----------|--------|----------------|
| CPU      | 2 vCPU | 2 cores |
| RAM      | 2 GB   | 2 GB |
| Disk     | 2 GB   | 500 MB |

### Software

| Tool | Version | Required for |
|------|---------|--------------|
| `git` | any | Source checkout |
| `python3` | 3.10+ | Server + Qt app |
| `pip` | current | Python deps |
| `docker` | 24+ | Container deployment |
| `docker compose` | v2 | Container orchestration |
| `openjdk` | 17 | Android build |
| `Xcode` | 15+ | iOS / macOS build |
| `.NET SDK` | 8.0 | Windows build |

### Network

| Port | Service | Direction |
|------|---------|-----------|
| 80   | Nginx (full-stack Docker) | inbound |
| 443  | Nginx TLS (optional) | inbound |
| 5000 | Web Portal | inbound |
| 8080 | Cloud API | inbound |

---

## Python Server Installation

### Linux

Tested on **Ubuntu 22.04 / 24.04**, **Debian 12**, **Fedora 39+**, **Arch rolling**.

```bash
# Debian / Ubuntu
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git \
  libxcb-cursor0 libxkbcommon-x11-0 libgl1 libegl1

# Fedora / RHEL
sudo dnf install -y python3 python3-pip git \
  xcb-util-cursor libxkbcommon-x11 mesa-libGL mesa-libEGL

# Arch
sudo pacman -Sy --needed python python-pip git \
  xcb-util-cursor libxkbcommon-x11 mesa
```

```bash
git clone https://github.com/stillwell/MedPharm.git
cd MedPharm
./install.sh                 # automated installer — fastest path
```

Or install manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-cloud.txt
pip install reportlab
```

### macOS

```bash
xcode-select --install          # command-line tools
brew install python@3.12 git
git clone https://github.com/stillwell/MedPharm.git
cd MedPharm
./install.sh
```

The Qt desktop application runs natively on Apple Silicon and Intel Macs via PyQt6 wheels.

### Windows (WSL 2)

Recommended for parity with Linux-based production deployments.

```powershell
# In PowerShell (as Administrator)
wsl --install -d Ubuntu-24.04
wsl --set-default-version 2
```

Inside the WSL shell, follow the [Linux](#linux) steps.

### Windows (native)

```powershell
winget install Python.Python.3.12
winget install Git.Git
git clone https://github.com/stillwell/MedPharm.git
cd MedPharm
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-cloud.txt
```

> The Qt desktop app runs on native Windows but requires the Visual C++ 2015–2022 redistributable which PyQt6 wheels pull in automatically. Web and API servers run on native Windows via Waitress or Gunicorn-on-WSL.

---

## Docker Installation

All Docker images are based on **Ubuntu 24.04 LTS**. Two images are published on Docker Hub:

| Image | Contents | Ports |
|-------|----------|-------|
| `enlightec/medpharm-api` | REST API only (Gunicorn) | 8080 |
| `enlightec/medpharm-server` | Nginx + API + Web Portal (Supervisor) | 80, 8080, 5000 |

### Single-command install

```bash
./install.sh --docker                     # API only
./install.sh --docker-server              # Full stack
./install.sh --docker --docker-server     # Both (auto-remaps ports)
./install.sh --docker --tag=1.7.6         # Pin version
```

### Compose (pre-built images)

```bash
docker compose -f docker-compose.hub.yml up -d                # API only
docker compose -f server/docker-compose.hub.yml up -d         # Full stack
```

### Compose (build from source)

```bash
docker compose up -d                                          # API only
cd server && docker compose up -d                             # Full stack
```

### Kubernetes (sketch)

The API container is 12-factor compliant — a minimal `Deployment`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: medpharm-api
spec:
  replicas: 2
  selector: { matchLabels: { app: medpharm-api } }
  template:
    metadata: { labels: { app: medpharm-api } }
    spec:
      containers:
        - name: api
          image: enlightec/medpharm-api:1.7.6
          ports: [{ containerPort: 8080 }]
          env:
            - { name: MEDPHARM_JWT_SECRET, valueFrom: { secretKeyRef: { name: medpharm, key: jwt } } }
          volumeMounts: [{ name: data, mountPath: /data }]
      volumes:
        - name: data
          persistentVolumeClaim: { claimName: medpharm-data }
```

---

## Database Initialization & Seeding

By default each component initialises its own private single-file SQLite database. To share **one** database across the Qt desktop, web portal, REST API, Docker, and Kubernetes, export a SQLAlchemy URL in `MEDPHARM_DATABASE_URL` (e.g. `postgresql+psycopg://medpharm:PASS@host:5432/medpharm`) before seeding — `DatabaseManager` then builds its engine from that URL instead of the SQLite file, and the seed steps below populate the shared database. Leave `MEDPHARM_DATABASE_URL` unset to keep the legacy private SQLite file.

`install.sh` does this automatically. To re-seed or seed manually:

```bash
source venv/bin/activate
python3 - <<'PY'
from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from database.seed_expanded import seed_expanded_data

db = DatabaseManager('medpharm_erp.db')
db.init_db()
seed_database(db)
seed_expanded_data(db)
print('Seed complete.')
PY
```

| Seed step | Adds |
|-----------|------|
| `init_db()` | 23 tables, 18 enums |
| `seed_database` | 55 medications, 24 interactions, 5 staff, 5 patients, sample prescriptions / invoices |
| `seed_expanded_data` | 30+ symptoms, 25+ conditions, 20+ additional medications |

To reset the database, stop all services and delete `medpharm_erp.db` (or the Docker `medpharm-data` volume) before re-seeding. This applies to the default SQLite deployment; with a shared `MEDPHARM_DATABASE_URL` PostgreSQL backend, reset the database server-side instead (e.g. `dropdb`/`createdb` or `DROP SCHEMA public CASCADE`) before re-running the seed.

---

## Client Runtime Installation

Installing the **pre-built** client binaries — to build them yourself see [COMPILATION.md](COMPILATION.md).

### Android

1. Download `app-release.apk` from the release page.
2. Enable *Install unknown apps* for your file manager.
3. Install and launch — point the app at your API host in Settings.

### iOS

Distribute via **TestFlight** for beta, or via **App Store Connect** for production. Sideloading with Xcode requires a free or paid Apple Developer account.

### macOS

Drop the `.app` bundle into `/Applications`. If Gatekeeper blocks the unsigned build, run:

```bash
xattr -dr com.apple.quarantine /Applications/MedPharm.app
```

### Windows

Install via the generated MSI or self-contained exe. Requires .NET 8 Desktop Runtime (auto-installed by the MSI).

---

## Post-Installation Verification

All installs terminate TLS by default (HIPAA § 164.312(e)(1)). Use `-k` while you are running against the dev-generated self-signed cert; drop `-k` once a CA-issued cert is mounted.

```bash
# API health (API-only container, gunicorn TLS)
curl -sk https://localhost:8080/api/v1/health | jq .

# API health (full server stack, Nginx TLS)
curl -sk https://localhost/api/v1/health | jq .

# HTTP -> HTTPS redirect (full server stack only)
curl -sI http://localhost/api/v1/health | head -1     # expect 301

# Staff login smoke test
curl -sk -X POST https://localhost:8080/api/v1/auth/login/staff \
  -H 'Content-Type: application/json' \
  -d '{"username":"dr.carter","password":"doctor123"}' | jq .

# Web portal reachability
curl -skI https://localhost/portal/ | head -1
```

Expected responses:

| Check | Expected |
|-------|----------|
| `https://…/api/v1/health` | `{"status":"ok"}` |
| `http://localhost/` (server stack) | `HTTP/1.1 301 Moved Permanently` → `https://localhost/` |
| Staff login | JSON with `access_token`, `refresh_token` |
| Web portal | `HTTP/1.1 200 OK` or `302` (login page redirect) |

### Database & TLS configuration knobs

| Env var | Default | Purpose |
|---------|---------|---------|
| `MEDPHARM_DATABASE_URL` | _(unset)_ | Full SQLAlchemy URL of a shared database, e.g. `postgresql+psycopg://user:pass@host:5432/medpharm`. When set, every server-side component shares this one database and `MEDPHARM_DB_PATH` is ignored. Unset → private SQLite. |
| `MEDPHARM_DB_PATH` | `medpharm_erp.db` | Path to the SQLite database (used only when `MEDPHARM_DATABASE_URL` is unset) |
| `MEDPHARM_DB_PASSWORD` | `change-this-in-production` | Password for the Docker Compose `db` (PostgreSQL 16) service / `medpharm-postgres` StatefulSet and the `MEDPHARM_DATABASE_URL` it builds |
| `MEDPHARM_TLS_MODE` | `auto` | `auto` (generate self-signed if none present), `require` (fail if no cert mounted), `disable` (plaintext — dev only) |
| `MEDPHARM_TLS_DIR` | `/etc/ssl/medpharm` | Directory containing `fullchain.pem` + `privkey.pem` |
| `MEDPHARM_TLS_HOSTNAME` | `localhost` | CN / SAN for self-signed generation |
| `MEDPHARM_TLS_DAYS` | `825` | Validity for auto-generated self-signed certs |

For **production** always use a CA-issued cert (Let's Encrypt, ACM, corporate PKI). Never ship a production deployment with a self-signed cert — browsers and mobile clients will refuse the connection and training users to click past warnings is itself a compliance failure.

---

## Uninstallation

The repository ships with `uninstall.sh`, a companion to `install.sh` that reverses every artifact the installer creates. It never touches tracked source files (launcher scripts, `.env.example`, docs, Dockerfiles) — for a fully pristine tree use `git clean -fdx`.

### Quick reference

```bash
./uninstall.sh                             # Interactive — remove venv, DB, log
./uninstall.sh --force                     # Non-interactive source cleanup
./uninstall.sh --keep-data                 # Remove venv but preserve data/medpharm.db
./uninstall.sh --docker --docker-volumes   # Tear down API-only container + persistent volume
./uninstall.sh --all --force               # Scorched earth — no prompts, no confirmations
```

### What `uninstall.sh` removes

| Artifact | Removed by default | Flag to change |
|----------|--------------------|----------------|
| `venv/`                     | ✓ | — |
| `data/medpharm.db` + empty `data/` | ✓ | `--keep-data` |
| `install.log`               | ✓ | — |
| `__pycache__/` (project-side, excludes `venv/`) | ✓ | — |
| `*.pyc` (project-side) | ✓ | — |
| `${TMPDIR}/medpharm_test_install.db` stray test DB | ✓ | — |
| `server/.env` (contains JWT / session secrets) | ✗ | `--remove-env` |
| Docker container `medpharm-api` (API-only) | ✗ | `--docker` / `--docker-api` |
| Docker container `medpharm-server` (full stack) | ✗ | `--docker-server` / `--docker-full` |
| Docker volumes `medpharm-data`, `medpharm-logs` (plus project-prefixed variants) | ✗ | `--docker-volumes` |
| Images `enlightec/medpharm-api`, `enlightec/medpharm-server` (all cached tags) | ✗ | `--docker-images` |

### Flag reference

| Flag | Effect |
|------|--------|
| `-f` / `--force` / `--yes` | Skip every confirmation prompt (auto-enabled under non-interactive shells / CI). |
| `--keep-data`              | Preserve `data/medpharm.db` and the `data/` directory. |
| `--remove-env`             | Also delete `server/.env` (kept by default — contains your generated secrets). |
| `--docker`, `--docker-api` | Run `docker compose -f docker-compose.hub.yml down` and force-remove the `medpharm-api` container if it lingers. |
| `--docker-server`, `--docker-full` | Same for `server/docker-compose.hub.yml` / `medpharm-server`. |
| `--docker-volumes`         | Remove named volumes after containers stop. **Deletes persisted DB data.** |
| `--docker-images`          | Remove every locally cached tag of `enlightec/medpharm-api` and `enlightec/medpharm-server`. |
| `--all`                    | Expands to `--docker --docker-server --docker-volumes --docker-images --remove-env`. |
| `-h` / `--help`            | Print usage and exit. |

Every run writes an audit trail to `uninstall.log` (timestamped, one line per action).

### Reinstall after uninstall

```bash
./install.sh --fresh
```

### Manual equivalents (if you cannot run `uninstall.sh`)

```bash
# Source install cleanup
deactivate 2>/dev/null
rm -rf venv data install.log
find . -type d -name __pycache__ -not -path './venv/*' -exec rm -rf {} +

# Docker Hub cleanup
docker compose -f docker-compose.hub.yml down
docker compose --env-file server/.env -f server/docker-compose.hub.yml down
docker volume rm medpharm-data medpharm-logs 2>/dev/null || true
docker image rm enlightec/medpharm-api enlightec/medpharm-server 2>/dev/null || true
```

---

## Troubleshooting

| Symptom | Resolution |
|---------|------------|
| `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"` | Install `libxcb-cursor0 libxkbcommon-x11-0` on Debian/Ubuntu. |
| `ImportError: libGL.so.1` | Install `libgl1` / `mesa-libGL`. |
| `Address already in use` on 8080 | `sudo lsof -i :8080` then stop the conflicting process or set `MEDPHARM_PORT`. |
| `sqlite3.OperationalError: database is locked` | A SQLite-only condition (concurrent writers / DB on NFS). Stop competing processes or move the DB off NFS — or point every component at a networked PostgreSQL via `MEDPHARM_DATABASE_URL`, which handles concurrent writers and so avoids this lock entirely. |
| 401 on every API call | Clear and refresh tokens — expired access tokens must be renewed via `POST /auth/refresh`. |
| CORS error from mobile client | Set `MEDPHARM_CORS_ORIGINS` to include the client origin, restart API. |
| Docker port clash | Use `./install.sh --docker --docker-server` (auto-remaps) or override `MEDPHARM_PORT`. |
