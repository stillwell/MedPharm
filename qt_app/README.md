# MedPharm — Qt Desktop Application (Clinical Staff)

PyQt6 desktop client for doctors, psychiatrists, pharmacists, and admins. Runs on Linux (X11 / Wayland), macOS, and Windows.

Feature inventory: [`docs/CLIENTS.md § Qt Desktop`](../docs/CLIENTS.md#qt-desktop-clinical-staff).
Runtime setup: [`docs/INSTALLATION.md`](../docs/INSTALLATION.md).

---

## Module layout

```
qt_app/
├── main_window.py              # QMainWindow, sidebar navigation, role-based visibility
├── styles.py                   # Dark-theme QSS (teal accents)
├── dialogs/
│   └── login_dialog.py         # Staff authentication dialog
└── widgets/
    ├── dashboard_widget.py     # KPIs, today's schedule, recent activity
    ├── patient_widget.py       # Master-detail, 7-tab profile panel
    ├── prescription_widget.py  # Rx creation + interaction checking
    ├── medication_widget.py    # 75+ medication catalog
    ├── appointment_widget.py   # Calendar scheduling
    ├── records_widget.py       # Type-filtered medical records
    ├── billing_widget.py       # Invoices + insurance claims
    ├── symptoms_widget.py      # Symptoms + conditions reference
    └── analytics_widget.py     # 4 matplotlib chart panels
```

Unlike the mobile clients, the Qt app talks **directly to `DatabaseManager`** — no REST hop.

---

## Run

```bash
../start_desktop.sh
# or
source ../venv/bin/activate
python3 ../run_qt.py
```

A login dialog appears. Staff credentials are listed in the top-level [README](../README.md#default-credentials).

---

## Role-based features

| Role | Access |
|------|--------|
| Doctor | All clinical widgets, analytics |
| Psychiatrist | All clinical widgets, analytics |
| Pharmacist | Medications, Prescriptions, Billing |
| Admin | All widgets + user management |

Role is resolved at login and drives the sidebar visibility in `main_window.py`.

---

## Styling

`styles.py` is a single QSS string applied globally in `main_window.py`. To override the accent colour, edit `ACCENT_COLOR` at the top of the file.

---

## Packaging

To build a stand-alone binary:

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name MedPharm-Desktop \
  --add-data "qt_app/styles.py:qt_app" \
  --add-data "database:database" \
  ../run_qt.py
```

See [`docs/COMPILATION.md § Python Components`](../docs/COMPILATION.md#python-components).

---

## Requirements

* Python 3.10+
* PyQt6 ≥ 6.6
* matplotlib ≥ 3.8
* numpy ≥ 1.26
* SQLAlchemy ≥ 2.0
* X11 / Wayland on Linux · Quartz on macOS · DWM on Windows
