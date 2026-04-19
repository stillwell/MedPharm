# MedPharm ERP

**Medical & Pharmaceutical Enterprise Resource Planning System**

A multi-platform ERP system for medical practices and pharmacies, featuring native clients for Android, iOS, macOS, and Windows, a PyQt6 desktop application for clinical staff, a Flask web portal for patients, and a cloud REST API backend. Built on a unified SQLAlchemy database with 75+ real-world medications, 30+ symptoms, 25+ conditions, drug interaction checking, insurance claims, prescription management, billing, and analytics.

Developed by **Robert Andrew Stillwell** at [Enlightec Ltd.](https://www.enlightec.com)

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Docker Hub Images](#docker-hub-images)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Documentation](#documentation)
- [Default Credentials](#default-credentials)
- [License](#license)

---

## Features

### Qt6 Desktop Application (Clinical Staff)
- **Dashboard** — Real-time KPIs, today's appointments, recent activity with 60-second auto-refresh
- **Patient Management** — Master-detail view with demographics, vitals, allergies, diagnoses, and 7-tab detail panel
- **Prescriptions** — Create prescriptions with automatic drug-drug interaction checking across 24 known interaction pairs
- **Medication Database** — Searchable catalog of 75+ FDA-referenced medications with NDC codes, scheduling, and pricing
- **Appointments** — Calendar-based scheduling with status management (scheduled, checked-in, in-progress, completed, cancelled)
- **Medical Records** — Patient-filtered clinical records with type-based filtering
- **Billing** — Invoice management, payment recording, insurance claim submission and processing, and revenue summary
- **Symptoms & Conditions** — Searchable medical reference database with 30+ symptoms and 25+ conditions, body system filtering, and emergency indicators
- **Analytics** — Four interactive matplotlib charts: revenue trends, patient demographics, top medications, and provider workload

### Cloud REST API (Mobile & Desktop Clients)
- **JWT Authentication** — HMAC-SHA256 token-based auth with access/refresh tokens, patient and staff login flows
- **Patient Self-Service** — Dashboard, prescriptions, billing, records, appointments, medications, profile, notifications
- **Staff Endpoints** — Dashboard, patient management, prescriptions, appointments, analytics (revenue, demographics, top meds)
- **Insurance Claims** — Submit claims, view claim status, staff claim processing with approved/denied/paid workflow
- **Medical Reference** — Searchable symptoms and conditions database with body system and category filtering
- **Medication Search** — Full medication catalog search by name, drug class, or schedule
- **CORS-enabled** — Configurable origins for cross-platform client access
- **Production-ready** — Gunicorn support, environment variable configuration, health check endpoint

### Android Application (Kotlin)
- **MVVM Architecture** — ViewModel + LiveData + Repository pattern with Retrofit/OkHttp networking
- **Patient Portal** — Dashboard, prescriptions with refill requests, billing with payments, appointments, medical records
- **Insurance Claims** — File claims against invoices using on-file insurance records
- **Medication Browser** — Searchable medication reference database
- **Security** — EncryptedSharedPreferences for token storage, OkHttp auth interceptor for automatic token injection
- **Material Design** — Material 3 components, dark theme, swipe-to-refresh, bottom navigation

### iOS Application (SwiftUI)
- **Native SwiftUI** — Async/await networking, NavigationStack, searchable modifiers
- **Patient Portal** — Dashboard with KPI cards, prescriptions with refill, billing with payment sheet, appointments, records
- **Insurance Claims** — File claims with insurance picker and submit via REST API
- **Keychain Storage** — Secure token persistence via iOS Keychain Services
- **Tab Navigation** — Dashboard, Prescriptions, Billing, Appointments, and More (records, medications, symptoms, profile)

### macOS Application (SwiftUI)
- **NavigationSplitView** — Native macOS sidebar navigation with master-detail layout
- **Full Feature Parity** — Dashboard, prescriptions, billing, appointments, records, medications, insurance claims, profile
- **SwiftUI Table** — Native macOS table components for prescriptions and medications
- **Shared Codebase** — Shares Models and APIClient with the iOS application

### Windows Desktop Application (.NET 8 / WPF)
- **MVVM with CommunityToolkit** — Clean architecture with HttpClient, Newtonsoft.Json, DPAPI token encryption
- **Sidebar Navigation** — Dashboard, prescriptions, billing, appointments, insurance claims
- **Payment & Claims** — Pay invoices and file insurance claims with provider selection
- **DPAPI Security** — Windows Data Protection API for encrypted token storage

### Flask Web Portal (Patients)
- **Secure Registration** — 4-factor patient identity verification (name, date of birth, SSN last 4, insurance ID)
- **Prescription Viewer** — Active, past, and detailed prescription views with refill request capability
- **Bill Pay** — View invoices and submit payments with credit card, debit card, or ACH
- **Medical Records** — Browse personal records filtered by type
- **Appointments** — View upcoming and past appointment history
- **Medication Info** — Current medications with dosage, frequency, and drug information
- **Profile Management** — Update contact info, insurance details, and allergy records

### Database & Backend
- **23 SQLAlchemy ORM models** with 18 Python enums and full relationship mapping
- **75+ real medications** seeded with NDC codes, drug classes, schedules, and pricing
- **24 drug-drug interactions** with severity levels and clinical descriptions
- **30+ symptoms** with body system classification and emergency indicators
- **25+ conditions** with ICD-10 codes, categories, and prevalence data
- **Insurance claims workflow** — SUBMITTED → IN_REVIEW → APPROVED → PAID / DENIED with automatic payment creation
- **PBKDF2-SHA256 password hashing** via Werkzeug
- **Role-based access control** — Doctor, Psychiatrist, Pharmacist, Admin, and Patient roles
- **Audit logging** for compliance tracking

---

## Architecture

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Android    │ │     iOS      │ │    macOS     │ │   Windows    │
│   (Kotlin)   │ │  (SwiftUI)   │ │  (SwiftUI)   │ │  (.NET/WPF)  │
│   Material 3 │ │  Async/Await │ │  NavSplit    │ │  MVVM/DPAPI  │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │
       └────────────────┴────────┬───────┴────────────────┘
                                 ▼
                    ┌────────────────────────┐
                    │   Flask REST API       │
                    │   /api/v1/*            │
                    │   JWT + CORS           │
                    │   (run_cloud.py)       │
                    └───────────┬────────────┘
                                │
┌─────────────────────┐         │         ┌─────────────────────┐
│   PyQt6 Desktop     │         │         │   Flask Web Portal   │
│   (Clinical Staff)  │         │         │   (Patients)         │
└────────┬────────────┘         │         └──────────┬───────────┘
         │                      │                    │
         └──────────────┬───────┴────────────────────┘
                        ▼
              ┌─────────────────────┐
              │   DatabaseManager   │
              │   (SQLAlchemy 2.0)  │
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │   SQLite Database   │
              │   23 Models         │
              │   75+ Medications   │
              │   30+ Symptoms      │
              │   25+ Conditions    │
              │   24 Interactions   │
              └─────────────────────┘
```

---

## Project Structure

```
MedPharm/
├── __init__.py
├── run_qt.py                  # Desktop application launcher
├── run_web.py                 # Web portal launcher
├── run_cloud.py               # Cloud API server launcher
├── install.sh                 # Automated installer (cross-platform)
├── uninstall.sh               # Companion uninstaller — reverses install.sh
├── start_desktop.sh           # Desktop quick-launch script
├── start_web.sh               # Web portal quick-launch script
├── start_cloud.sh             # Cloud API quick-launch script
├── generate_docs.sh           # PDF documentation generator script
├── requirements.txt           # Qt desktop + web portal dependencies
├── requirements-cloud.txt     # Cloud API server dependencies
├── Dockerfile                 # Docker image (API only, Ubuntu 24.04)
├── docker-compose.yml         # Docker Compose — API (build from source)
├── docker-compose.hub.yml     # Docker Compose — API (pull from Docker Hub)
├── start_docker_hub.sh        # Interactive launcher for Docker Hub images
├── .dockerignore              # Docker build exclusions
├── LICENSE                    # GNU General Public License v3.0
│
├── .github/workflows/
│   └── docker-publish.yml     # CI/CD: build & push to Docker Hub
│
├── server/                    # ── Docker Server Package ───────
│   ├── Dockerfile             # Full stack (Ubuntu 24.04 LTS)
│   ├── docker-compose.yml     # Full stack — build from source
│   ├── docker-compose.hub.yml # Full stack — pull from Docker Hub
│   ├── entrypoint.sh          # DB init & process bootstrap
│   ├── healthcheck.sh         # Docker health check script
│   ├── supervisord.conf       # Process manager config
│   ├── requirements-server.txt# Combined server dependencies
│   ├── .env.example           # Environment variable template
│   ├── .dockerignore          # Server build exclusions
│   └── nginx/
│       └── medpharm.conf      # Nginx reverse proxy config
│
├── database/
│   ├── models.py              # 23 SQLAlchemy ORM models & 18 enums
│   ├── db_manager.py          # DatabaseManager — all CRUD & business logic
│   ├── seed_data.py           # 55 medications, 24 interactions, sample data
│   └── seed_expanded.py       # 30+ symptoms, 25+ conditions, 20+ additional meds
│
├── api/
│   ├── app.py                 # Cloud API Flask application factory
│   ├── auth.py                # JWT HMAC-SHA256 authentication
│   └── routes.py              # REST API endpoints (/api/v1/*)
│
├── qt_app/
│   ├── main_window.py         # QMainWindow with sidebar navigation
│   ├── styles.py              # Dark theme QSS stylesheet (teal accents)
│   ├── dialogs/
│   │   └── login_dialog.py    # Staff authentication dialog
│   └── widgets/
│       ├── dashboard_widget.py
│       ├── patient_widget.py
│       ├── prescription_widget.py
│       ├── medication_widget.py
│       ├── appointment_widget.py
│       ├── records_widget.py
│       ├── billing_widget.py  # Includes insurance claim submission
│       ├── symptoms_widget.py # Symptoms & conditions reference browser
│       └── analytics_widget.py
│
├── web/
│   ├── app.py                 # Flask application factory
│   ├── routes.py              # All route handlers & API endpoints
│   ├── static/
│   │   ├── css/style.css      # Dark theme portal stylesheet
│   │   └── js/app.js          # Client-side interactions
│   └── templates/             # 14 Jinja2 templates
│
├── android/                   # Android app (Kotlin, MVVM, Retrofit)
│   └── app/src/main/
│       ├── java/com/enlightec/medpharm/
│       │   ├── data/          # API service, repository, models
│       │   ├── ui/            # Fragments, ViewModels, Adapters
│       │   └── util/          # AuthInterceptor, Resource wrapper
│       └── res/               # Layouts, drawables, strings, themes
│
├── ios/                       # iOS app (SwiftUI, async/await)
│   └── MedPharm/MedPharm/
│       ├── Models/            # Codable data models
│       ├── Services/          # APIClient, AuthManager, KeychainHelper
│       └── Views/             # SwiftUI views by feature
│
├── macos/                     # macOS app (SwiftUI, NavigationSplitView)
│   └── MedPharm/MedPharm/
│       ├── Models/            # Shared with iOS
│       ├── Services/          # APIClient, AuthManager
│       └── Views/             # macOS-optimized views
│
├── windows/                   # Windows app (.NET 8, WPF)
│   └── MedPharm/
│       ├── Models/            # API data models
│       ├── Services/          # ApiClient, TokenStore (DPAPI)
│       └── Views/             # XAML pages and dialogs
│
└── docs/
    ├── generate_pdf.py                    # ReportLab PDF generator
    └── MedPharm_ERP_Documentation.pdf     # Technical reference
```

---

## Requirements

### Server / Desktop (Python)
- **Python 3.10+**
- **Operating System:** Ubuntu/Debian, Fedora/RHEL, macOS, Arch Linux, or Windows (WSL)
- **Display server** required for the Qt desktop application (X11 or Wayland)

### Python Dependencies

| Package      | Version  | Purpose                        |
|-------------|----------|--------------------------------|
| PyQt6       | >= 6.6.0 | Desktop GUI framework          |
| Flask       | >= 3.0.0 | Web portal + Cloud API         |
| flask-cors  | >= 4.0.0 | CORS support for REST API      |
| SQLAlchemy  | >= 2.0.0 | ORM and database management    |
| Werkzeug    | >= 3.0.0 | Password hashing & WSGI        |
| matplotlib  | >= 3.8.0 | Analytics charts               |
| numpy       | >= 1.26.0| Numerical support for charts   |
| gunicorn    | >= 21.2.0| Production WSGI server         |
| ReportLab   | >= 4.0   | PDF documentation generation   |

### Mobile / Desktop Clients

| Platform | Language | Min Version | Key Dependencies |
|----------|----------|-------------|------------------|
| Android  | Kotlin   | API 26+     | Retrofit, OkHttp, Coroutines, EncryptedSharedPreferences |
| iOS      | Swift    | iOS 16+     | SwiftUI, async/await, Keychain Services |
| macOS    | Swift    | macOS 13+   | SwiftUI, NavigationSplitView |
| Windows  | C#       | .NET 8      | WPF, Newtonsoft.Json, CommunityToolkit.Mvvm, DPAPI |

---

## Installation

### Automated Install (Recommended)

The install script handles OS detection, Python version checking, virtual environment creation, dependency installation, database initialization, and integration tests.

```bash
git clone https://github.com/stillwell/MedPharm.git
cd MedPharm
chmod +x install.sh
./install.sh
```

The installer will:
1. Detect your operating system and install system-level dependencies
2. Verify Python 3.10+ is available
3. Create a virtual environment in `venv/`
4. Install all Python packages including flask-cors for cloud API support
5. Initialize the SQLite database and seed it with sample data
6. Seed expanded reference data (symptoms, conditions, additional medications)
7. Run integration tests to verify everything works
8. Preserve the tracked launcher scripts (`start_web.sh`, `start_desktop.sh`, `start_cloud.sh`, `generate_docs.sh`) — fallback templates with full GPL headers are only written when a launcher is missing from the working tree

### Uninstallation

The repository ships with `uninstall.sh`, which reverses every artifact `install.sh` creates. Tracked source files (launcher scripts, `.env.example`, docs, Dockerfiles) are never touched.

```bash
./uninstall.sh                             # Interactive — remove venv, DB, log, __pycache__
./uninstall.sh --force                     # Non-interactive (for CI / scripting)
./uninstall.sh --keep-data                 # Preserve data/medpharm.db
./uninstall.sh --docker --docker-volumes   # Tear down API-only container + persistent volume
./uninstall.sh --all --force               # Scorched earth: containers, volumes, images, env, no prompts
./uninstall.sh --help                      # Full flag reference
```

Docker teardown is **opt-in** — nothing Docker-related runs unless you pass `--docker`, `--docker-server`, `--docker-volumes`, `--docker-images`, or `--all`. See [docs/INSTALLATION.md](docs/INSTALLATION.md#uninstallation) for the full flag matrix.

To reinstall after uninstalling:

```bash
./install.sh --fresh
```

### Manual Install

```bash
git clone https://github.com/stillwell/MedPharm.git
cd MedPharm

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-cloud.txt
pip install reportlab

# Initialize the database
python3 -c "
import sys, os
sys.path.insert(0, os.getcwd())
from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from database.seed_expanded import seed_expanded_data
db = DatabaseManager('medpharm_erp.db')
db.init_db()
seed_database(db)
seed_expanded_data(db)
print('Database initialized with sample data.')
"
```

### Docker Deployment (Ubuntu 24.04 LTS)

Both Docker images run on **Ubuntu Server 24.04 LTS** and are published to Docker Hub under the [`enlightec`](https://hub.docker.com/u/enlightec) namespace. You can either **pull pre-built images** (fastest, recommended) or **build from source** using the included Dockerfiles.

#### Option A — Pull Pre-built Images from Docker Hub (Recommended)

No local build required. Pull the images and start a container in under a minute.

**One-line install** (uses the included installer):

```bash
./install.sh --docker                     # API only (port 8080)
./install.sh --docker-server              # Full stack: Nginx + API + Patient Portal (port 80)
./install.sh --docker --docker-server     # Both at once (API on 8080 + Full stack on 80)
```

Both `--docker` and `--docker-server` can be combined in a single invocation. When combined, the full-stack container's direct API host port is auto-remapped from `8080` to `8081` to avoid clashing with the API-only container that already owns `8080`. The full-stack Nginx entry point remains on port `80`, and the direct Patient Portal port remains on `5000`.

**Interactive quick-launch helper:**

```bash
./start_docker_hub.sh           # Menu — choose API only, full stack, pull, or stop
./start_docker_hub.sh api       # Start API-only container
./start_docker_hub.sh server    # Start full stack
./start_docker_hub.sh pull      # Pull both images without starting
./start_docker_hub.sh stop      # Stop all MedPharm containers
```

**Manual docker compose (API only)** — uses `docker-compose.hub.yml`:

```bash
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
curl http://localhost:8080/api/v1/health
```

**Manual docker compose (Full stack)** — uses `server/docker-compose.hub.yml`:

```bash
cd server
cp .env.example .env                              # Edit secrets before production
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
curl http://localhost/api/v1/health
```

**Pull without docker compose:**

```bash
docker pull enlightec/medpharm-server:latest    # Full stack
docker pull enlightec/medpharm-api:latest       # API only

# Pin to a specific release
docker pull enlightec/medpharm-api:1.5.1
```

**Run directly with `docker run`:**

```bash
# API only
docker run -d --name medpharm-api \
  -p 8080:8080 \
  -v medpharm-data:/data \
  -e MEDPHARM_JWT_SECRET=your-secret-here \
  -e MEDPHARM_SECRET_KEY=your-other-secret \
  enlightec/medpharm-api:latest

# Full stack
docker run -d --name medpharm-server \
  -p 80:80 -p 8080:8080 -p 5000:5000 \
  -v medpharm-data:/data \
  -v medpharm-logs:/var/log/medpharm \
  -e MEDPHARM_JWT_SECRET=your-secret-here \
  -e MEDPHARM_SECRET_KEY=your-other-secret \
  enlightec/medpharm-server:latest
```

#### Option B — Build from Source

If you want to build the images locally (e.g., to make source modifications):

**Full Server Stack** (Nginx + Cloud API + Web Portal):

```bash
cd server
cp .env.example .env      # Edit secrets before production use
docker compose up -d       # Build from server/Dockerfile and start
docker compose logs -f     # View logs
```

**API Only** (lightweight, no Nginx):

```bash
docker compose up -d       # Build from root Dockerfile, starts API on port 8080
```

Services available (either option):

| Endpoint | Description |
|----------|-------------|
| `http://localhost/api/v1/health` | REST API via Nginx (full stack only) |
| `http://localhost/portal/` | Web Portal via Nginx (full stack only) |
| `http://localhost:8080/` | API direct access |
| `http://localhost:5000/` | Web Portal direct access (full stack only) |

#### Option C — Combined Deployment (API + Full Stack Simultaneously)

You can run the API-only image **and** the full-stack image on the same host in a single installer invocation:

```bash
./install.sh --docker --docker-server
```

Both sets of flags after the same `./install.sh` command are parsed together. The installer auto-remaps the full-stack container's direct API host port from `8080` → `8081` so it does not collide with the API-only container that owns `8080`.

Resulting endpoints when both deployments are active:

| Endpoint | Container | Description |
|----------|-----------|-------------|
| `http://localhost:8080/api/v1` | `enlightec/medpharm-api` | Standalone REST API (default) |
| `http://localhost/` | `enlightec/medpharm-server` | Full-stack Nginx entry point |
| `http://localhost/api/v1/health` | `enlightec/medpharm-server` | Full-stack API via Nginx |
| `http://localhost/portal/` | `enlightec/medpharm-server` | Patient Portal via Nginx |
| `http://localhost:8081/` | `enlightec/medpharm-server` | Full-stack API direct (remapped from 8080) |
| `http://localhost:5000/` | `enlightec/medpharm-server` | Patient Portal direct |

Stop both deployments:

```bash
docker compose -f docker-compose.hub.yml down
docker compose -f server/docker-compose.hub.yml down
```

### CI/CD Pipeline (GitHub Actions)

Docker images are automatically built and pushed to Docker Hub on every tagged release. The pipeline:

1. **Validates source code** — Syntax checks all Python modules, tests database initialization, verifies API health check and web portal login page
2. **Builds & pushes** two images to Docker Hub:
   - `enlightec/medpharm-server:<version>` — Full stack (Nginx + API + Web Portal)
   - `enlightec/medpharm-api:<version>` — API only

**To trigger a release:**

```bash
git tag v1.2.0
git push origin v1.2.0   # Triggers the pipeline
```

**Required GitHub Secrets** (set in Settings > Secrets and variables > Actions):

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username (e.g., `enlightec`) |
| `DOCKERHUB_TOKEN` | Docker Hub access token ([create one here](https://hub.docker.com/settings/security)) |

### Building Mobile / Desktop Clients

**Android:**
```bash
cd android
./gradlew assembleDebug
```

**iOS / macOS:**
Open `ios/MedPharm/MedPharm.xcodeproj` or `macos/MedPharm/MedPharm.xcodeproj` in Xcode and build.

**Windows:**
```bash
cd windows/MedPharm
dotnet build
dotnet run
```

---

## Docker Hub Images

MedPharm ERP publishes two official container images to Docker Hub under the **[enlightec](https://hub.docker.com/u/enlightec)** namespace. Both images are built from the Dockerfiles in this repository and are tagged on every versioned release (`v*.*.*`).

### Published Images

| Image | Docker Hub | Contents | Base | Exposed Ports |
|-------|------------|----------|------|---------------|
| [`enlightec/medpharm-server:latest`](https://hub.docker.com/r/enlightec/medpharm-server) | [hub.docker.com/r/enlightec/medpharm-server](https://hub.docker.com/r/enlightec/medpharm-server) | Nginx + Cloud REST API + Patient Web Portal (Supervisor-managed) | Ubuntu 24.04 LTS | `80`, `8080`, `5000` |
| [`enlightec/medpharm-api:latest`](https://hub.docker.com/r/enlightec/medpharm-api) | [hub.docker.com/r/enlightec/medpharm-api](https://hub.docker.com/r/enlightec/medpharm-api) | Cloud REST API only (Gunicorn) | Ubuntu 24.04 LTS | `8080` |

All images are available at [https://hub.docker.com/u/enlightec](https://hub.docker.com/u/enlightec) and can be browsed at [https://hub.docker.com/repositories/enlightec](https://hub.docker.com/repositories/enlightec).

### Supported Tags

| Tag | Description |
|-----|-------------|
| `latest` | Most recent release |
| `1.5.1`, `1.1.1`, `1.1.0`, `1.0.0` | Pinned semantic version tags (published from `v*.*.*` git tags) |

### Quick Pull

```bash
docker pull enlightec/medpharm-server:latest
docker pull enlightec/medpharm-api:latest

# Pin to a specific release
docker pull enlightec/medpharm-api:1.5.1
```

### Quick Start

The fastest way to run MedPharm without any local Python setup:

```bash
git clone https://github.com/stillwell/MedPharm.git
cd MedPharm

# Option 1 — interactive menu
./start_docker_hub.sh

# Option 2 — direct flags
./start_docker_hub.sh api        # API only on port 8080
./start_docker_hub.sh server     # Full stack on port 80

# Option 3 — installer
./install.sh --docker                     # API only
./install.sh --docker-server              # Full stack
./install.sh --docker --docker-server     # Both (API on 8080 + Full stack on 80)
./install.sh --docker --tag=1.5.1         # Pin to a specific release
```

### Compose Files for Docker Hub Images

The repository ships two compose files that reference the Docker Hub images (no build step):

| File | Purpose |
|------|---------|
| `docker-compose.hub.yml` | API-only deployment (`enlightec/medpharm-api`) |
| `server/docker-compose.hub.yml` | Full stack deployment (`enlightec/medpharm-server`) |

```bash
# API only
docker compose -f docker-compose.hub.yml up -d

# Full stack
cd server && docker compose -f docker-compose.hub.yml up -d
```

### Persistent Data & Volumes

Both images use named Docker volumes so your data survives container restarts and re-pulls:

| Volume | Mount Point | Purpose |
|--------|-------------|---------|
| `medpharm-data` | `/data` | SQLite database (`medpharm_erp.db`) |
| `medpharm-logs` | `/var/log/medpharm` | Nginx + Supervisor logs (full stack only) |

### Image Rebuilds

Docker images are automatically rebuilt and published to Docker Hub by the [GitHub Actions workflow](.github/workflows/docker-publish.yml) on every tagged release. See the [CI/CD Pipeline](#cicd-pipeline-github-actions) section for details.

---

## Quick Start

### Start via Docker Hub (Zero-Build)

Skip the Python build entirely and run the official images directly:

```bash
./start_docker_hub.sh server     # Full stack at http://localhost
./start_docker_hub.sh api        # API only at http://localhost:8080
```

See [Docker Hub Images](#docker-hub-images) for more options.

### Start the Cloud API Server (Required for Mobile/Desktop Clients)

```bash
./start_cloud.sh
```

Or manually:
```bash
source venv/bin/activate
python3 run_cloud.py
```

The API server starts at **http://localhost:8080/api/v1**. All Android, iOS, macOS, and Windows clients connect to this endpoint.

### Start the Web Portal (Patient Interface)

```bash
./start_web.sh
```

Or manually:
```bash
source venv/bin/activate
python3 run_web.py
```

Open your browser to **http://localhost:5000** and log in with one of the patient accounts listed in [Default Credentials](#default-credentials).

### Start the Desktop Application (Clinical Staff)

```bash
./start_desktop.sh
```

Or manually:
```bash
source venv/bin/activate
python3 run_qt.py
```

A login dialog will appear. Use one of the staff credentials listed in [Default Credentials](#default-credentials).

### Custom Port for Web Portal

Pass the port as an argument:
```bash
./start_web.sh 8080
```

---

## Usage Guide

### Cloud API — Mobile & Desktop Client Access

The REST API provides JWT-authenticated endpoints for all client platforms:

- **Authentication:** `POST /api/v1/auth/login/patient`, `POST /api/v1/auth/login/staff`, `POST /api/v1/auth/register`
- **Patient Endpoints:** `/api/v1/patient/dashboard`, `/prescriptions`, `/billing`, `/records`, `/appointments`, `/profile`, `/notifications`
- **Insurance Claims:** `POST /api/v1/patient/insurance/claims` to submit, `GET` to list, staff can process via `/staff/insurance/claims/<id>/process`
- **Reference Data:** `/api/v1/reference/symptoms`, `/reference/conditions`, `/medications/search`
- **Staff Endpoints:** `/api/v1/staff/dashboard`, `/patients`, `/appointments`, `/prescriptions`, `/analytics/*`

All endpoints require a `Bearer <token>` Authorization header except `/health`, `/auth/*`.

### Desktop Application — Clinical Staff Workflow

1. **Login** — Authenticate with your staff credentials. Access is role-based (Doctor, Psychiatrist, Pharmacist, Admin).

2. **Dashboard** — After login, the dashboard shows key performance indicators (active patients, pending prescriptions, today's appointments, monthly revenue), today's schedule, and recent activity. Data refreshes automatically every 60 seconds.

3. **Patient Management** — The left panel lists all patients with a search bar. Select a patient to view their full profile in the right panel, which is organized into 7 tabs: Demographics, Vitals, Allergies, Diagnoses, Prescriptions, Billing, and Records. Click "Add Patient" to register a new patient.

4. **Prescriptions** — View all prescriptions or create new ones. The prescription dialog lets you select a patient, add multiple medication lines, and set dosage/frequency/duration/quantity for each. When you add medications, the system automatically checks for drug-drug interactions and displays warnings with severity levels. Saving a prescription auto-generates a priced invoice.

5. **Medication Database** — Browse and search the full catalog of 75+ medications. Filter by drug class or schedule. Select any medication to view detailed information including NDC code, manufacturer, dosage forms, pricing, and contraindications.

6. **Appointments** — A calendar widget on the left lets you pick a date. Appointments for that date appear on the right. Create new appointments or update their status through the workflow: Scheduled → Checked In → In Progress → Completed.

7. **Medical Records** — Select a patient and filter records by type (lab results, imaging, clinical notes, etc.).

8. **Billing** — View all invoices with status indicators (Pending, Partial, Paid, Overdue). Record payments against invoices. Submit and process insurance claims with approval/denial workflow. Summary cards show total billed, collected, and outstanding amounts.

9. **Symptoms & Conditions** — Browse the medical reference database. Search symptoms by name or body system with emergency indicators. Search conditions by name, ICD-10 code, or category. Select any entry to view detailed information including associated conditions, typical medications, and prevalence data.

10. **Analytics** — Four chart panels powered by matplotlib: monthly revenue trends, patient age/gender demographics, top prescribed medications, and provider workload distribution.

### Web Portal — Patient Workflow

1. **Register** — New patients verify their identity using 4 factors: first name, last name, date of birth, and last 4 digits of SSN. These must match an existing patient record in the system. Once verified, create a username and password.

2. **Login** — Log in with your portal credentials.

3. **Dashboard** — View a summary of active prescriptions, upcoming appointments, and recent invoices at a glance.

4. **Prescriptions** — Browse active, past, and all prescriptions. View full details including medications, dosages, refill counts, and costs. Request refills for eligible medications directly from the detail page.

5. **Billing** — View all invoices and their payment status. Click "Pay" on any invoice with an outstanding balance to submit a payment via credit card, debit card, or bank account (ACH).

6. **Records** — Access your medical records filtered by type.

7. **Appointments** — View upcoming and past appointments with date, time, provider, and status.

8. **Medications** — See your current medications with full details: dosage, frequency, drug class, manufacturer, and special instructions.

9. **Profile** — Update your phone number, email, and address. View insurance information and manage allergy records.

---

## Documentation

A comprehensive technical reference PDF is included with the project. It covers the complete system architecture, source code walkthroughs, database schema, security controls, deployment guide, and API reference.

### View the PDF

The pre-generated PDF is located at:
```
docs/MedPharm_ERP_Documentation.pdf
```

### Regenerate the PDF

To regenerate the documentation (e.g., after making changes):

```bash
./generate_docs.sh
```

Or manually:
```bash
source venv/bin/activate
python3 docs/generate_pdf.py
```

The PDF includes:
- System architecture overview with component diagrams
- Complete database schema with all 23 models and relationships
- Multi-platform client architecture (Android, iOS, macOS, Windows)
- Cloud REST API endpoint reference with authentication details
- Insurance claims workflow documentation
- Drug interaction checking algorithm walkthrough
- Flask web portal route reference
- Qt desktop application module documentation
- Security control matrix (JWT auth, HMAC-SHA256, DPAPI, Keychain, password hashing, audit logging)
- Deployment and configuration guide
- Links to external documentation (SQLAlchemy, Flask, PyQt6, Retrofit, SwiftUI, WPF)

---

## Default Credentials

### Desktop Application & Cloud API (Staff)

| Role          | Username     | Password    |
|--------------|-------------|-------------|
| Doctor       | dr.carter   | doctor123   |
| Doctor       | dr.chen     | doctor123   |
| Psychiatrist | dr.brooks   | doctor123   |
| Pharmacist   | pharm.davis | pharm123    |
| Admin        | admin       | admin123    |

### Web Portal, Mobile & Desktop Clients (Patients)

| Patient             | Username          | Password    |
|--------------------|-------------------|-------------|
| John Smith         | jsmith_portal     | patient123  |
| Maria Johnson      | mjohnson_portal   | patient123  |
| Emily Williams     | ewilliams_portal  | patient123  |
| Sarah Davis        | sdavis_portal     | patient123  |
| Linda Martinez     | lmartinez_portal  | patient123  |

> **Note:** These are demo credentials for development and testing. Change all passwords before any production deployment.

---

## Environment Variables

The cloud API server and Docker deployment can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MEDPHARM_DB_PATH` | `medpharm_erp.db` | Path to SQLite database |
| `MEDPHARM_SECRET_KEY` | Auto-generated | Flask secret key |
| `MEDPHARM_JWT_SECRET` | Dev default | JWT signing secret (change in production) |
| `MEDPHARM_TOKEN_EXPIRY` | `86400` | Access token lifetime in seconds (24h) |
| `MEDPHARM_REFRESH_EXPIRY` | `604800` | Refresh token lifetime in seconds (7 days) |
| `MEDPHARM_CORS_ORIGINS` | `*` | Allowed CORS origins |
| `MEDPHARM_HOST` | `0.0.0.0` | Server bind host |
| `MEDPHARM_PORT` | `8080` | Server bind port |
| `MEDPHARM_DEBUG` | `false` | Enable debug mode |
| `MEDPHARM_HTTP_PORT` | `80` | Nginx listen port (Docker full stack) |
| `MEDPHARM_API_PORT` | `8080` | Gunicorn API port (Docker full stack) |
| `MEDPHARM_WEB_PORT` | `5000` | Gunicorn Web Portal port (Docker full stack) |
| `MEDPHARM_WORKERS` | `4` | Gunicorn worker processes |
| `MEDPHARM_THREADS` | `2` | Gunicorn threads per worker |

---

## License

This project is licensed under the **GNU General Public License v3.0**.

Copyright (C) 2026 [Enlightec Ltd.](https://www.enlightec.com)
Author: Robert Andrew Stillwell
Email: Andrew.Stillwell@enlightec.com

See the [LICENSE](LICENSE) file for the full license text.

---

<p align="center">
  <strong>MedPharm ERP</strong> — Built by <a href="https://www.enlightec.com">Enlightec Ltd.</a>
</p>
