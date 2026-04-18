# MedPharm — Database Package

Single source of truth for MedPharm's persistent state. Every server component (Cloud API, Web Portal, Qt Desktop) accesses data exclusively through `DatabaseManager`.

---

## Module layout

| File | Responsibility |
|------|----------------|
| `models.py` | 23 SQLAlchemy ORM models, 18 Python enums |
| `db_manager.py` | `DatabaseManager` — CRUD, business logic, interaction checks, claims workflow |
| `seed_data.py` | Base seed: 55 medications, 24 interactions, 5 staff, 5 patients, sample Rx/invoices |
| `seed_expanded.py` | Expansion pack: 30+ symptoms, 25+ conditions, 20+ additional medications |

---

## Core tables

| Table | Role |
|-------|------|
| `users` | Staff accounts (roles: doctor, psychiatrist, pharmacist, admin) |
| `patients` | Patient demographics + portal credentials |
| `medications` | Catalog — NDC, class, schedule, price |
| `medication_interactions` | Known drug-drug interactions with severity |
| `prescriptions` / `prescription_items` | Rx headers + line items |
| `appointments` | Scheduled visits with status lifecycle |
| `medical_records` | Notes, labs, imaging, procedures |
| `invoices` / `invoice_items` / `payments` | Billing & revenue |
| `insurance_providers` / `patient_insurance` / `insurance_claims` | Claims workflow |
| `allergies` / `vitals` / `diagnoses` | Clinical observations |
| `symptoms` / `conditions` | Reference dataset |
| `audit_logs` | Compliance / access trail |

23 models total. See `models.py` for full relationships.

---

## Initialise a fresh database

```python
from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from database.seed_expanded import seed_expanded_data

db = DatabaseManager('medpharm_erp.db')
db.init_db()                 # CREATE TABLE IF NOT EXISTS
seed_database(db)            # Base data
seed_expanded_data(db)       # Expansion pack
```

---

## Backends

`DatabaseManager` accepts any SQLAlchemy URL. Default: SQLite at `medpharm_erp.db`.

| Backend | URL example |
|---------|------------|
| SQLite (default) | `sqlite:///medpharm_erp.db` |
| PostgreSQL | `postgresql+psycopg://user:pass@host/medpharm` |
| MySQL | `mysql+pymysql://user:pass@host/medpharm` |

For multi-writer deployments migrate off SQLite. Schema is portable; only the initial `init_db()` differs.

---

## Insurance claims state machine

```
SUBMITTED ─► IN_REVIEW ─► APPROVED ─► PAID
                       └► DENIED
```

`DatabaseManager.process_claim(claim_id, action, approved_amount, notes)` enforces the transitions and auto-creates a `Payment` row when a claim reaches `APPROVED` → `PAID`.

---

## Drug interaction algorithm

On `create_prescription(...)`:

1. Collect medication IDs in the new Rx.
2. For each pair `(a, b)` (unordered), query `medication_interactions`.
3. Return a list of `InteractionWarning` objects with severity (`MINOR`, `MODERATE`, `MAJOR`, `CONTRAINDICATED`).
4. The Qt desktop app blocks save on `CONTRAINDICATED` and warns on `MAJOR`.

---

## Migrations

Schema evolves additively — `CREATE TABLE IF NOT EXISTS` in `init_db()` creates new tables on upgrade. Destructive changes (column drops / renames) require a manual SQL migration script. For major revisions, introduce Alembic (`alembic init db/migrations`) and version `models.py` with `alembic revision --autogenerate`.
