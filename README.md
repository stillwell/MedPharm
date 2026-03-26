# MedPharm ERP

**Medical & Pharmaceutical Enterprise Resource Planning System**

A full-stack ERP platform for medical practices and pharmacies, featuring a PyQt6 desktop application for clinical staff and a Flask web portal for patients. Built on a unified SQLAlchemy database with 55 real-world medications, drug interaction checking, prescription management, billing, and analytics.

Developed by **Robert Andrew Stillwell** at [Enlightec Ltd.](https://www.enlightec.com)

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
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
- **Medication Database** — Searchable catalog of 55 FDA-referenced medications with NDC codes, scheduling, and pricing
- **Appointments** — Calendar-based scheduling with status management (scheduled, checked-in, in-progress, completed, cancelled)
- **Medical Records** — Patient-filtered clinical records with type-based filtering
- **Billing** — Invoice management, payment recording, and revenue summary
- **Analytics** — Four interactive matplotlib charts: revenue trends, patient demographics, top medications, and provider workload

### Flask Web Portal (Patients)
- **Secure Registration** — 4-factor patient identity verification (name, date of birth, SSN last 4, insurance ID)
- **Prescription Viewer** — Active, past, and detailed prescription views with refill request capability
- **Bill Pay** — View invoices and submit payments with credit card, debit card, or ACH
- **Medical Records** — Browse personal records filtered by type
- **Appointments** — View upcoming and past appointment history
- **Medication Info** — Current medications with dosage, frequency, and drug information
- **Profile Management** — Update contact info, insurance details, and allergy records

### Database & Backend
- **20 SQLAlchemy ORM models** with 16 Python enums and full relationship mapping
- **55 real medications** seeded with NDC codes, drug classes, schedules, and pricing
- **24 drug-drug interactions** with severity levels and clinical descriptions
- **PBKDF2-SHA256 password hashing** via Werkzeug
- **Role-based access control** — Doctor, Psychiatrist, Pharmacist, Admin, and Patient roles
- **Audit logging** for compliance tracking

---

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   PyQt6 Desktop     │     │   Flask Web Portal   │
│   (Clinical Staff)  │     │   (Patients)         │
│                     │     │                      │
│  - Dashboard        │     │  - Prescriptions     │
│  - Patients         │     │  - Bill Pay          │
│  - Prescriptions    │     │  - Records           │
│  - Medications      │     │  - Appointments      │
│  - Appointments     │     │  - Profile           │
│  - Billing          │     │                      │
│  - Analytics        │     │                      │
└────────┬────────────┘     └──────────┬───────────┘
         │                             │
         └──────────┐   ┌──────────────┘
                    ▼   ▼
          ┌─────────────────────┐
          │   DatabaseManager   │
          │   (SQLAlchemy 2.0)  │
          └──────────┬──────────┘
                     ▼
          ┌─────────────────────┐
          │   SQLite Database   │
          │   (20 Models)       │
          │   55 Medications    │
          │   24 Interactions   │
          └─────────────────────┘
```

---

## Project Structure

```
medical_erp/
├── __init__.py
├── run_qt.py                  # Desktop application launcher
├── run_web.py                 # Web portal launcher
├── install.sh                 # Automated installer (cross-platform)
├── start_desktop.sh           # Desktop quick-launch script
├── start_web.sh               # Web portal quick-launch script
├── generate_docs.sh           # PDF documentation generator script
├── requirements.txt
│
├── database/
│   ├── models.py              # 20 SQLAlchemy ORM models & 16 enums
│   ├── db_manager.py          # DatabaseManager — all CRUD & business logic
│   └── seed_data.py           # 55 medications, 24 interactions, sample data
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
│       ├── billing_widget.py
│       └── analytics_widget.py
│
├── web/
│   ├── app.py                 # Flask application factory
│   ├── routes.py              # All route handlers & API endpoints
│   ├── static/
│   │   ├── css/style.css      # Dark theme portal stylesheet
│   │   └── js/app.js          # Client-side interactions
│   └── templates/             # 14 Jinja2 templates
│       ├── base.html
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html
│       ├── prescriptions.html
│       ├── prescription_detail.html
│       ├── billing.html
│       ├── pay.html
│       ├── records.html
│       ├── appointments.html
│       ├── medications.html
│       ├── profile.html
│       └── errors/
│           ├── 404.html
│           └── 500.html
│
└── docs/
    ├── generate_pdf.py                    # ReportLab PDF generator
    └── MedPharm_ERP_Documentation.pdf     # 31-page technical reference
```

---

## Requirements

- **Python 3.10+**
- **Operating System:** Ubuntu/Debian, Fedora/RHEL, macOS, or Arch Linux
- **Display server** required for the desktop application (X11 or Wayland)

### Python Dependencies

| Package      | Version  | Purpose                        |
|-------------|----------|--------------------------------|
| PyQt6       | >= 6.6.0 | Desktop GUI framework          |
| Flask       | >= 3.0.0 | Web portal framework           |
| SQLAlchemy  | >= 2.0.0 | ORM and database management    |
| Werkzeug    | >= 3.0.0 | Password hashing & WSGI        |
| matplotlib  | >= 3.8.0 | Analytics charts               |
| numpy       | >= 1.26.0| Numerical support for charts   |
| ReportLab   | >= 4.0   | PDF documentation generation   |

---

## Installation

### Automated Install (Recommended)

The install script handles OS detection, Python version checking, virtual environment creation, dependency installation, database initialization, and integration tests.

```bash
git clone https://github.com/robert-andrew-stillwell/MedPharm.git
cd MedPharm
chmod +x install.sh
./install.sh
```

The installer will:
1. Detect your operating system and install system-level dependencies
2. Verify Python 3.10+ is available
3. Create a virtual environment in `venv/`
4. Install all Python packages from `requirements.txt` plus ReportLab
5. Initialize the SQLite database and seed it with sample data
6. Run integration tests to verify everything works
7. Create quick-launch scripts (`start_web.sh`, `start_desktop.sh`, `generate_docs.sh`)

### Manual Install

```bash
git clone https://github.com/robert-andrew-stillwell/MedPharm.git
cd MedPharm

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install reportlab

# Initialize the database
python3 -c "
import sys, os
sys.path.insert(0, os.path.dirname(os.getcwd()))
from medical_erp.database.db_manager import DatabaseManager
from medical_erp.database.seed_data import seed_database
db = DatabaseManager('medpharm_erp.db')
db.init_db()
seed_database(db)
print('Database initialized with sample data.')
"
```

---

## Quick Start

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

### Desktop Application — Clinical Staff Workflow

1. **Login** — Authenticate with your staff credentials. Access is role-based (Doctor, Psychiatrist, Pharmacist, Admin).

2. **Dashboard** — After login, the dashboard shows key performance indicators (active patients, pending prescriptions, today's appointments, monthly revenue), today's schedule, and recent activity. Data refreshes automatically every 60 seconds.

3. **Patient Management** — The left panel lists all patients with a search bar. Select a patient to view their full profile in the right panel, which is organized into 7 tabs: Demographics, Vitals, Allergies, Diagnoses, Prescriptions, Billing, and Records. Click "Add Patient" to register a new patient.

4. **Prescriptions** — View all prescriptions or create new ones. The prescription dialog lets you select a patient, add multiple medication lines, and set dosage/frequency/duration/quantity for each. When you add medications, the system automatically checks for drug-drug interactions and displays warnings with severity levels. Saving a prescription auto-generates a priced invoice.

5. **Medication Database** — Browse and search the full catalog of 55 medications. Filter by drug class or schedule. Select any medication to view detailed information including NDC code, manufacturer, dosage forms, pricing, and contraindications. Export the catalog to CSV.

6. **Appointments** — A calendar widget on the left lets you pick a date. Appointments for that date appear on the right. Create new appointments or update their status through the workflow: Scheduled → Checked In → In Progress → Completed.

7. **Medical Records** — Select a patient and filter records by type (lab results, imaging, clinical notes, etc.).

8. **Billing** — View all invoices with status indicators (Pending, Partial, Paid, Overdue). Record payments against invoices. Summary cards show total billed, collected, and outstanding amounts.

9. **Analytics** — Four chart panels powered by matplotlib: monthly revenue trends, patient age/gender demographics, top prescribed medications, and provider workload distribution.

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

A comprehensive 31-page technical reference PDF is included with the project. It covers the complete system architecture, source code walkthroughs, database schema, security controls, deployment guide, and API reference with clickable web links to external documentation.

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
- Complete database schema with all 20 models and relationships
- Step-by-step source code explanations with annotated code blocks
- Drug interaction checking algorithm walkthrough
- Flask web portal route reference
- Qt desktop application module documentation
- Security control matrix (authentication, authorization, hashing, audit logging)
- Deployment and configuration guide
- Links to external documentation (SQLAlchemy, Flask, PyQt6, HIPAA, FDA, OWASP)

---

## Default Credentials

### Desktop Application (Staff)

| Role          | Username     | Password    |
|--------------|-------------|-------------|
| Doctor       | dr.carter   | doctor123   |
| Psychiatrist | dr.brooks   | doctor123   |
| Pharmacist   | pharm.davis | pharm123    |
| Admin        | admin       | admin123    |

### Web Portal (Patients)

| Patient             | Username          | Password    |
|--------------------|-------------------|-------------|
| John Smith         | jsmith_portal     | patient123  |
| Maria Johnson      | mjohnson_portal   | patient123  |
| Emily Williams     | ewilliams_portal  | patient123  |

> **Note:** These are demo credentials for development and testing. Change all passwords before any production deployment.

---

## License

This project is licensed under the **GNU General Public License v3.0**.

Copyright (C) 2026 [Enlightec Ltd.](https://www.enlightec.com)
Author: Robert Andrew Stillwell

See the [LICENSE](LICENSE) file for the full license text.

---

<p align="center">
  <strong>MedPharm ERP</strong> — Built by <a href="https://www.enlightec.com">Enlightec Ltd.</a>
</p>
