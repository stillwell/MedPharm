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

"""
MedPharm ERP - Demonstration Dataset (``seed_demo``)

Completes the demo so that *every* screen a doctor or a patient sees in a
demonstration build is populated with internally-consistent data. It runs
*after* :func:`database.seed_data.seed_database` (15 patients, prescriptions,
records, appointments, invoices) and fills the gaps that base seed leaves:

  1. **Symptoms & Conditions catalogue** — the clinical reference screens are
     empty until :func:`database.seed_expanded.seed_expanded_data` runs.
  2. **Provider NPIs** — backfills the three prescribers' CMS NPIs so the
     NPI-on-prescription workflow shows real identifiers.
  3. **Today's appointment board** — a full day of appointments dated *today*
     across providers and statuses, so the staff dashboard's "Today's Appts"
     KPI and list are alive whenever the demo is opened.
  4. **Insurance claims** — one claim per existing invoice, spanning the whole
     adjudication lifecycle (submitted → in-review → approved →
     partially-approved → denied → paid), each tied to the patient's real
     insurer. The *denied* Adderall XR claim explains its overdue invoice.

Everything is **idempotent and additive** — safe to run on every launch.

The companion :func:`delete_demo_data` (CLI ``--delete``) clears the example
PHI layer — every patient and everything that hangs off them — while keeping
the medication / symptom / condition reference catalogue and the staff login
accounts, leaving a working but patient-free install. That is exactly what
``./uninstall.sh --demo-data-delete`` invokes.

CLI::

    python -m database.seed_demo                 # enrich the default database
    python -m database.seed_demo --all-dbs       # enrich both SQLite files
    python -m database.seed_demo --delete --yes  # wipe the example PHI layer
    python -m database.seed_demo --delete --dry-run
    python -m database.seed_demo --db data/medpharm.db
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, time, timedelta

# Allow both ``python -m database.seed_demo`` and ``python database/seed_demo.py``.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.models import (
    User, Patient, Insurance, Appointment, Invoice, InsuranceClaim,
    AppointmentType, AppointmentStatus, InsuranceClaimStatus,
)

# Free-text marker stamped on rows this module creates, so the today-board can
# be recognised on a re-run (idempotency) and audited later.
DEMO_TAG = "[demo-data]"

# CMS NPIs that pass the NPPES Luhn check (see DatabaseManager.validate_npi).
# Mirrors the values database/seed_data.py assigns; demo use only.
PROVIDER_NPIS = {
    "dr.carter": "1000000004",
    "dr.chen": "1234567893",
    "dr.brooks": "1472583693",
}

# Per-invoice claim plan. Keyed by the trailing digits of the invoice number so
# it survives id renumbering. The denied Adderall XR claim (INV-…05) is *why*
# that invoice is OVERDUE in the base seed — a deliberate, coherent link.
CLAIM_PLAN = {
    "00000001": InsuranceClaimStatus.PAID,
    "00000002": InsuranceClaimStatus.SUBMITTED,
    "00000003": InsuranceClaimStatus.IN_REVIEW,
    "00000004": InsuranceClaimStatus.APPROVED,
    "00000005": InsuranceClaimStatus.DENIED,
    "00000006": InsuranceClaimStatus.SUBMITTED,
    "00000007": InsuranceClaimStatus.PAID,
    "00000008": InsuranceClaimStatus.PARTIALLY_APPROVED,
}
# Fallback rotation for any invoice not named in CLAIM_PLAN.
_CLAIM_FALLBACK = [
    InsuranceClaimStatus.SUBMITTED,
    InsuranceClaimStatus.IN_REVIEW,
    InsuranceClaimStatus.APPROVED,
    InsuranceClaimStatus.PAID,
]

# Today's appointment board. (patient last name, provider username, type,
# hour, minute, status, reason) — reasons track each patient's real diagnosis.
_TODAY_BOARD = [
    ("Smith",    "dr.carter", AppointmentType.FOLLOW_UP,       8, 30, AppointmentStatus.COMPLETED,   "Hypertension follow-up — BP recheck"),
    ("Brown",    "dr.carter", AppointmentType.MEDICATION_REVIEW, 9, 15, AppointmentStatus.IN_PROGRESS, "Type 2 diabetes — HbA1c & statin review"),
    ("Johnson",  "dr.brooks", AppointmentType.FOLLOW_UP,      10,  0, AppointmentStatus.CONFIRMED,   "Depression follow-up — PHQ-9"),
    ("Wilson",   "dr.carter", AppointmentType.CONSULTATION,   11,  0, AppointmentStatus.CONFIRMED,   "Asthma management — inhaler technique"),
    ("Davis",    "dr.brooks", AppointmentType.FOLLOW_UP,      13, 30, AppointmentStatus.SCHEDULED,   "ADHD medication check — BP & weight"),
    ("Anderson", "dr.carter", AppointmentType.FOLLOW_UP,      15,  0, AppointmentStatus.SCHEDULED,   "Atrial fibrillation & thyroid review"),
    ("Williams", "dr.brooks", AppointmentType.FOLLOW_UP,      16,  0, AppointmentStatus.SCHEDULED,   "Generalized anxiety follow-up — GAD-7"),
]


# ── helpers ────────────────────────────────────────────────────────────────

class _Log:
    """Tiny prefixed logger; quiet mode swallows everything."""

    def __init__(self, quiet: bool = False):
        self.quiet = quiet

    def __call__(self, msg: str) -> None:
        if not self.quiet:
            print(f"  [seed_demo] {msg}")


def _users_by_username(session) -> dict[str, User]:
    return {u.username: u for u in session.query(User).all()}


def _patients_by_lastname(session) -> dict[str, Patient]:
    """Last name → first matching patient. The base roster has unique last
    names, so this is unambiguous for the demo board."""
    out: dict[str, Patient] = {}
    for p in session.query(Patient).order_by(Patient.id).all():
        out.setdefault(p.last_name, p)
    return out


# ── enrichment steps ───────────────────────────────────────────────────────

def _ensure_reference_catalogue(dm: DatabaseManager, log: _Log) -> None:
    """Populate the Symptoms & Conditions reference screens if they're empty."""
    from database.models import Symptom, Condition
    with dm.get_session() as s:
        have = (s.query(Symptom).count(), s.query(Condition).count())
    if all(have):
        log(f"reference catalogue present ({have[0]} symptoms, {have[1]} conditions)")
        return
    from database.seed_expanded import seed_expanded_data
    seed_expanded_data(dm)
    with dm.get_session() as s:
        log(f"seeded reference catalogue "
            f"({s.query(Symptom).count()} symptoms, {s.query(Condition).count()} conditions)")


def _ensure_provider_npis(dm: DatabaseManager, log: _Log) -> int:
    """Backfill prescriber NPIs (no-op where already set)."""
    changed = 0
    with dm.get_session() as s:
        for username, npi in PROVIDER_NPIS.items():
            u = s.query(User).filter_by(username=username).first()
            if u and not u.npi:
                u.npi = npi
                changed += 1
    log(f"provider NPIs backfilled: {changed}")
    return changed


def _ensure_today_appointments(dm: DatabaseManager, log: _Log) -> int:
    """Add a full day of appointments dated today (idempotent via DEMO_TAG)."""
    with dm.get_session() as s:
        already = s.query(Appointment).filter(
            Appointment.notes.like(f"%{DEMO_TAG}%"),
            Appointment.scheduled_datetime >= datetime.combine(date.today(), time.min),
            Appointment.scheduled_datetime <= datetime.combine(date.today(), time.max),
        ).count()
        if already:
            log(f"today's board already present ({already} appointments)")
            return 0

        users = _users_by_username(s)
        patients = _patients_by_lastname(s)
        added = 0
        for last, uname, atype, hh, mm, status, reason in _TODAY_BOARD:
            patient = patients.get(last)
            provider = users.get(uname)
            if not (patient and provider):
                continue
            s.add(Appointment(
                patient_id=patient.id,
                provider_id=provider.id,
                appointment_type=atype,
                scheduled_datetime=datetime.combine(date.today(), time(hh, mm)),
                duration_minutes=30,
                status=status,
                reason=reason,
                notes=DEMO_TAG,
            ))
            added += 1
    log(f"today's appointment board added: {added}")
    return added


def _ensure_insurance_claims(dm: DatabaseManager, log: _Log) -> int:
    """Create one claim per invoice (whose patient carries insurance) that has
    none yet, spanning the full adjudication lifecycle."""
    added = 0
    with dm.get_session() as s:
        claimed_invoice_ids = {
            row[0] for row in s.query(InsuranceClaim.invoice_id).all()
        }
        invoices = s.query(Invoice).order_by(Invoice.invoice_number).all()
        fallback_i = 0
        for inv in invoices:
            if inv.id in claimed_invoice_ids:
                continue
            insurance = s.query(Insurance).filter_by(
                patient_id=inv.patient_id, is_active=True).first()
            if not insurance:
                continue

            suffix = inv.invoice_number.rsplit("-", 1)[-1]
            status = CLAIM_PLAN.get(suffix)
            if status is None:
                status = _CLAIM_FALLBACK[fallback_i % len(_CLAIM_FALLBACK)]
                fallback_i += 1

            total = float(inv.total_amount or 0)
            copay = float(insurance.copay_amount or 0)
            provider = insurance.provider_name
            claim = InsuranceClaim(
                invoice_id=inv.id,
                insurance_id=insurance.id,
                patient_id=inv.patient_id,
                claim_number=f"CLM-{suffix}",
                status=status,
                submitted_date=date.today() - timedelta(days=18),
                claimed_amount=total,
                copay_amount=copay,
                notes=f"{DEMO_TAG} ",
            )
            _apply_claim_economics(claim, status, total, copay, provider)
            s.add(claim)
            added += 1
    log(f"insurance claims created: {added}")
    return added


def _ensure_recent_payments(dm: DatabaseManager, log: _Log) -> int:
    """Spread the example payments across the last several months — with one
    dated today — so the dashboard revenue KPIs and the Analytics revenue-trend
    chart aren't flat-zero. Only re-dates existing payments (invents no money),
    keeping each invoice's single payment consistent with its amount_paid.

    Idempotent: once a completed payment falls in the current month, it stops.
    """
    from database.models import Payment, PaymentStatus
    now = datetime.now()
    month_start = datetime.combine(now.date().replace(day=1), time.min)
    with dm.get_session() as s:
        if s.query(Payment).filter(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.payment_date >= month_start).count():
            log("recent payments already present (current month)")
            return 0
        pays = (s.query(Payment)
                .filter(Payment.status == PaymentStatus.COMPLETED)
                .order_by(Payment.amount.desc()).all())
        if not pays:
            log("no payments to re-date")
            return 0
        # Largest collection lands today; the rest fan out over recent months.
        offsets = [0, 6, 20, 48, 80, 110, 140, 170]
        for i, p in enumerate(pays):
            days = offsets[i] if i < len(offsets) else offsets[-1] + 30 * (i - len(offsets) + 1)
            p.payment_date = datetime.combine((now - timedelta(days=days)).date(), time(10, 30))
    log(f"payments dated across recent months: {len(pays)} (one today)")
    return len(pays)


def _apply_claim_economics(claim, status, total, copay, provider) -> None:
    """Fill amounts / dates / notes coherently for the claim's lifecycle stage."""
    insurer_portion = round(max(total - copay, 0.0), 2)
    responded = date.today() - timedelta(days=4)

    if status == InsuranceClaimStatus.SUBMITTED:
        claim.notes += f"Submitted to {provider}; awaiting adjudication."
    elif status == InsuranceClaimStatus.IN_REVIEW:
        claim.notes += f"Under review by {provider} claims department."
    elif status == InsuranceClaimStatus.APPROVED:
        claim.response_date = responded
        claim.approved_amount = insurer_portion
        claim.notes += f"Approved by {provider}; remittance pending. Patient copay ${copay:.2f}."
    elif status == InsuranceClaimStatus.PARTIALLY_APPROVED:
        approved = round(insurer_portion * 0.70, 2)
        claim.response_date = responded
        claim.approved_amount = approved
        claim.deductible_applied = round(insurer_portion - approved, 2)
        claim.notes += (f"Partially approved by {provider}; deductible applied. "
                        f"Patient responsible for the balance.")
    elif status == InsuranceClaimStatus.DENIED:
        claim.response_date = responded
        claim.approved_amount = 0
        claim.denial_reason = ("Prior authorization required for Adderall XR "
                               "(Schedule II stimulant) — none on file.")
        claim.notes += f"Denied by {provider}; resubmit with PA. Invoice left to patient."
    elif status == InsuranceClaimStatus.PAID:
        claim.response_date = responded
        claim.approved_amount = insurer_portion
        claim.notes += (f"Paid by {provider} (EOB on file); "
                        f"patient copay ${copay:.2f} collected.")


# ── public entry points ────────────────────────────────────────────────────

def seed_demo_data(dm: DatabaseManager, *, quiet: bool = False) -> dict:
    """Idempotently enrich an already base-seeded database into a complete demo.

    Returns a dict of how many rows each step added. No-op friendly: every step
    detects what is already present and only fills the gap.
    """
    log = _Log(quiet)
    with dm.get_session() as s:
        patient_count = s.query(Patient).count()
    if patient_count == 0:
        log("no patients found — run ./install.sh (or launch a client once) to "
            "load the base seed first; nothing to enrich.")
        return {"skipped": True}

    log(f"enriching demo data on {dm.safe_target}")
    # Each step is isolated: it opens its own session (rolled back on error) and
    # is wrapped here so one failure never aborts the others or crashes the
    # launcher that calls this on startup.
    steps = [
        ("reference_catalogue", _ensure_reference_catalogue),
        ("npis", _ensure_provider_npis),
        ("today_appointments", _ensure_today_appointments),
        ("insurance_claims", _ensure_insurance_claims),
        ("recent_payments", _ensure_recent_payments),
    ]
    result: dict = {}
    for name, fn in steps:
        try:
            result[name] = fn(dm, log)
        except Exception as exc:  # keep going; a demo extra must not break startup
            log(f"WARNING: step '{name}' failed and was skipped: {exc}")
            result[name] = f"error: {exc}"
    log("demo enrichment complete.")
    return result


# PHI / example-data tables, in child-before-parent (FK-safe) deletion order.
# Reference catalogue (medications, symptoms, conditions, interactions) and the
# staff `users` rows are intentionally NOT listed — they survive the wipe.
def _phi_delete_order():
    from database.models import (
        InsuranceClaim, Payment, InvoiceItem, Invoice, PrescriptionItem,
        Prescription, MedicalRecord, Appointment, Vital, Diagnosis, Allergy,
        LabResult, LabOrder, Immunization, CarePlan, Referral, SecureMessage,
        MessageThread, PatientConsent, ProviderNote, PatientDocument,
        EmergencyAccessGrantRec, PHIAccessLog, AuditLog,
        PatientPortalAccount, Insurance, Patient,
    )
    return [
        InsuranceClaim, Payment, InvoiceItem, Invoice,
        PrescriptionItem, Prescription, MedicalRecord, Appointment,
        Vital, Diagnosis, Allergy,
        LabResult, LabOrder, Immunization, CarePlan, Referral,
        SecureMessage, MessageThread, PatientConsent, ProviderNote,
        PatientDocument, EmergencyAccessGrantRec, PHIAccessLog, AuditLog,
        PatientPortalAccount, Insurance, Patient,
    ]


def delete_demo_data(dm: DatabaseManager, *, dry_run: bool = False,
                     quiet: bool = False) -> dict:
    """Remove the example PHI layer — every patient and all dependent records,
    plus the demo activity log — while preserving the medication / symptom /
    condition reference catalogue and the staff login accounts.

    Returns ``{tablename: rows_removed}``. With ``dry_run`` nothing is deleted;
    the dict reports what *would* be removed.
    """
    log = _Log(quiet)
    counts: dict[str, int] = {}
    models = _phi_delete_order()

    with dm.get_session() as s:
        for cls in models:
            n = s.query(cls).count()
            counts[cls.__tablename__] = n
            if n and not dry_run:
                s.query(cls).delete(synchronize_session=False)
        if dry_run:
            s.rollback()

    total = sum(counts.values())
    verb = "would remove" if dry_run else "removed"
    log(f"{verb} {total} example-data rows across {len(counts)} tables "
        f"on {dm.safe_target}")
    if not quiet:
        for table, n in counts.items():
            if n:
                print(f"      {verb}: {table:26} {n}")
    return counts


# ── target resolution + CLI ─────────────────────────────────────────────────

def _resolve_targets(db_arg: str | None, all_dbs: bool) -> list[DatabaseManager]:
    """Pick which database(s) to operate on.

    Precedence: MEDPHARM_DATABASE_URL (shared backend) > explicit --db >
    the SQLite files the launchers use (medpharm_erp.db, and data/medpharm.db
    when --all-dbs). Each returned manager is already ``init_db()``-ed.
    """
    url = os.environ.get("MEDPHARM_DATABASE_URL")
    if url:
        dm = DatabaseManager(database_url=url)
        dm.init_db()
        return [dm]

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if db_arg:
        paths = [db_arg]
    else:
        candidates = [
            os.path.join(root, "medpharm_erp.db"),
            os.path.join(root, "data", "medpharm.db"),
        ]
        present = [p for p in candidates if os.path.exists(p)]
        if all_dbs:
            paths = present or [candidates[0]]
        else:
            paths = [present[0]] if present else [candidates[0]]

    managers = []
    for p in paths:
        dm = DatabaseManager(db_path=p)
        dm.init_db()
        managers.append(dm)
    return managers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m database.seed_demo",
        description="Seed or delete the MedPharm ERP demonstration dataset.")
    parser.add_argument("--delete", action="store_true",
                        help="remove the example PHI layer instead of seeding it")
    parser.add_argument("--db", metavar="PATH",
                        help="operate on this SQLite file (default: the launcher DB)")
    parser.add_argument("--all-dbs", action="store_true",
                        help="operate on both medpharm_erp.db and data/medpharm.db")
    parser.add_argument("--dry-run", action="store_true",
                        help="with --delete, report what would be removed and stop")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="skip the confirmation prompt for --delete")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress progress output")
    args = parser.parse_args(argv)

    try:
        targets = _resolve_targets(args.db, args.all_dbs)
    except Exception as exc:  # pragma: no cover - configuration error path
        print(f"[seed_demo] could not open database: {exc}", file=sys.stderr)
        return 2

    if args.delete and not args.dry_run and not args.yes:
        where = ", ".join(dm.safe_target for dm in targets)
        print(f"This deletes ALL example patients and their records from: {where}")
        print("Reference catalogue (medications/symptoms/conditions) and staff "
              "logins are kept.")
        try:
            reply = input("Proceed? (y/N): ").strip().lower()
        except EOFError:
            reply = ""
        if reply not in ("y", "yes"):
            print("Aborted — nothing was changed.")
            return 1

    for dm in targets:
        if args.delete:
            delete_demo_data(dm, dry_run=args.dry_run, quiet=args.quiet)
        else:
            seed_demo_data(dm, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
