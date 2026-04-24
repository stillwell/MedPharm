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
MedPharm ERP - Flask Routes (Patient Portal)
"""

import uuid
from datetime import date, datetime
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, g, jsonify, current_app
)
from werkzeug.security import generate_password_hash

from security.csrf import csrf_required
from security.lockout import LockoutTracker, AccountLockedError
from security.passwords import validate_password, PasswordPolicy, PasswordPolicyError

portal_bp = Blueprint("portal", __name__)


_lockout_tracker: LockoutTracker | None = None


def _get_lockout() -> LockoutTracker:
    """Lazy, app-scoped lockout tracker keyed off the security config."""
    global _lockout_tracker
    if _lockout_tracker is None:
        cfg = current_app.config.get("SECURITY_CONFIG")
        if cfg is None:
            _lockout_tracker = LockoutTracker()
        else:
            _lockout_tracker = LockoutTracker(
                threshold=cfg.lockout_threshold,
                window_seconds=cfg.lockout_window_seconds,
                lockout_seconds=cfg.lockout_duration_seconds,
            )
    return _lockout_tracker


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("portal.login"))
        return f(*args, **kwargs)
    return wrapper


# ── Auth ───────────────────────────────────────────────────────────────────────

@portal_bp.route("/login", methods=["GET", "POST"])
@csrf_required
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        tracker = _get_lockout()
        key = f"portal:{username.lower()}"
        try:
            tracker.assert_not_locked(key)
        except AccountLockedError as exc:
            minutes = max(1, exc.retry_after // 60)
            flash(
                f"Too many failed login attempts. Try again in {minutes} minutes.",
                "danger"
            )
            return render_template("login.html")

        account = g.db_manager.authenticate_portal(username, password)
        if account:
            tracker.record_success(key)
            patient = g.db_manager.get_portal_patient(account["id"])
            session["user_id"] = account["id"]
            session["patient_id"] = account["patient_id"]
            session["username"] = account["username"]
            session["patient_name"] = patient["full_name"] if patient else username
            flash(f"Welcome back, {session['patient_name']}!", "success")
            return redirect(url_for("portal.dashboard"))

        remaining = tracker.record_failure(key)
        try:
            g.db_manager.record_failed_login(
                username=username, account_type="patient",
                ip=request.remote_addr or "",
                user_agent=request.headers.get("User-Agent", "")[:255],
                reason="bad_credentials",
            )
        except Exception:
            pass
        if remaining == 0:
            flash("Account temporarily locked due to too many failed attempts.",
                  "danger")
        else:
            flash(f"Invalid username or password. {remaining} attempts remaining.",
                  "danger")
    return render_template("login.html")


@portal_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("portal.login"))


@portal_bp.route("/register", methods=["GET", "POST"])
@csrf_required
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        dob_str = request.form.get("dob", "")
        ssn_last4 = request.form.get("ssn_last4", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([first_name, last_name, dob_str, ssn_last4, username, email, password]):
            flash("All fields are required.", "danger")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        cfg = current_app.config.get("SECURITY_CONFIG")
        policy = PasswordPolicy(
            min_length=cfg.password_min_length if cfg else 12,
        )
        try:
            validate_password(password, policy=policy, username=username)
        except PasswordPolicyError as exc:
            flash(f"Password rejected: {exc}", "danger")
            return render_template("register.html")

        try:
            dob = date.fromisoformat(dob_str)
        except ValueError:
            flash("Invalid date format.", "danger")
            return render_template("register.html")

        patient_id = g.db_manager.verify_patient_identity(first_name, last_name, dob, ssn_last4)
        if not patient_id:
            flash("Could not verify your identity. Please contact the office.", "danger")
            return render_template("register.html")

        try:
            g.db_manager.create_portal_account(patient_id, username, password, email)
            flash("Account created! You can now log in.", "success")
            return redirect(url_for("portal.login"))
        except Exception as e:
            flash(f"Registration failed: {e}", "danger")
    return render_template("register.html")


# ── Dashboard ──────────────────────────────────────────────────────────────────

@portal_bp.route("/dashboard")
@login_required
def dashboard():
    patient_id = session["patient_id"]
    prescriptions = g.db_manager.get_prescriptions_by_patient(patient_id)
    active_rx = [rx for rx in prescriptions if rx["status"] == "active"]
    invoices = g.db_manager.get_patient_invoices(patient_id)
    outstanding = sum(inv["balance_due"] for inv in invoices if inv["status"] in ("sent", "partial", "overdue"))
    appointments = g.db_manager.get_appointments(patient_id=patient_id)
    upcoming = [a for a in appointments if a["status"] in ("scheduled", "confirmed")]
    return render_template("dashboard.html",
        active_prescriptions=active_rx,
        outstanding_balance=outstanding,
        upcoming_appointments=upcoming[:5],
        recent_invoices=invoices[:5],
        prescription_count=len(active_rx),
        appointment_count=len(upcoming)
    )


# ── Prescriptions ─────────────────────────────────────────────────────────────

@portal_bp.route("/prescriptions")
@login_required
def prescriptions():
    patient_id = session["patient_id"]
    rxs = g.db_manager.get_prescriptions_by_patient(patient_id)
    active = [r for r in rxs if r["status"] == "active"]
    expired = [r for r in rxs if r["status"] in ("expired", "cancelled", "filled")]
    return render_template("prescriptions.html",
        active_prescriptions=active, past_prescriptions=expired, all_prescriptions=rxs)


@portal_bp.route("/prescriptions/<int:rx_id>")
@login_required
def prescription_detail(rx_id):
    rx = g.db_manager.get_prescription(rx_id)
    if not rx or rx["patient_id"] != session["patient_id"]:
        flash("Prescription not found.", "danger")
        return redirect(url_for("portal.prescriptions"))
    return render_template("prescription_detail.html", rx=rx)


@portal_bp.route("/prescriptions/<int:rx_id>/refill", methods=["POST"])
@login_required
@csrf_required
def request_refill(rx_id):
    rx = g.db_manager.get_prescription(rx_id)
    if not rx or rx["patient_id"] != session["patient_id"]:
        flash("Prescription not found.", "danger")
        return redirect(url_for("portal.prescriptions"))
    refilled = False
    for item in rx.get("items", []):
        if item["refills_remaining"] > 0:
            g.db_manager.refill_prescription_item(item["id"])
            refilled = True
    if refilled:
        flash("Refill request submitted successfully.", "success")
    else:
        flash("No refills remaining for this prescription.", "warning")
    return redirect(url_for("portal.prescription_detail", rx_id=rx_id))


# ── Billing ────────────────────────────────────────────────────────────────────

@portal_bp.route("/billing")
@login_required
def billing():
    patient_id = session["patient_id"]
    invoices = g.db_manager.get_patient_invoices(patient_id)
    payments = g.db_manager.get_payment_history(patient_id=patient_id)
    outstanding = sum(inv["balance_due"] for inv in invoices if inv["status"] in ("sent", "partial", "overdue"))
    return render_template("billing.html",
        invoices=invoices, payments=payments[:20], outstanding_balance=outstanding)


@portal_bp.route("/billing/<int:invoice_id>/pay", methods=["GET", "POST"])
@login_required
@csrf_required
def pay_bill(invoice_id):
    inv = g.db_manager.get_invoice(invoice_id)
    if not inv or inv["patient_id"] != session["patient_id"]:
        flash("Invoice not found.", "danger")
        return redirect(url_for("portal.billing"))

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            method = request.form.get("payment_method", "credit_card")
            if amount <= 0 or amount > inv["balance_due"]:
                flash("Invalid payment amount.", "danger")
                return render_template("pay.html", invoice=inv)

            g.db_manager.record_payment(
                invoice_id=invoice_id, amount=amount,
                payment_method=method,
                portal_account_id=session.get("user_id"),
                notes=f"Online payment via patient portal"
            )
            flash(f"Payment of ${amount:.2f} processed successfully!", "success")
            return redirect(url_for("portal.billing"))
        except Exception as e:
            flash(f"Payment failed: {e}", "danger")

    return render_template("pay.html", invoice=inv)


@portal_bp.route("/billing/history")
@login_required
def payment_history():
    payments = g.db_manager.get_payment_history(patient_id=session["patient_id"])
    return render_template("billing.html", payments=payments, invoices=[], outstanding_balance=0)


# ── Medical Records ────────────────────────────────────────────────────────────

@portal_bp.route("/records")
@login_required
def records():
    patient_id = session["patient_id"]
    record_type = request.args.get("type")
    all_records = g.db_manager.get_patient_records(patient_id, record_type)
    return render_template("records.html", records=all_records, selected_type=record_type or "all")


# ── Appointments ───────────────────────────────────────────────────────────────

@portal_bp.route("/appointments")
@login_required
def appointments():
    patient_id = session["patient_id"]
    all_appts = g.db_manager.get_appointments(patient_id=patient_id)
    upcoming = [a for a in all_appts if a["status"] in ("scheduled", "confirmed")]
    past = [a for a in all_appts if a["status"] in ("completed", "cancelled", "no_show")]
    return render_template("appointments.html", upcoming=upcoming, past=past)


# ── Medications ────────────────────────────────────────────────────────────────

@portal_bp.route("/medications")
@login_required
def medications():
    patient_id = session["patient_id"]
    rxs = g.db_manager.get_prescriptions_by_patient(patient_id)
    active_meds = []
    for rx in rxs:
        if rx["status"] == "active":
            for item in rx.get("items", []):
                med = g.db_manager.get_medication(item["medication_id"])
                if med:
                    active_meds.append({**item, **med, "prescriber_name": rx["prescriber_name"]})
    return render_template("medications.html", medications=active_meds)


# ── Profile ────────────────────────────────────────────────────────────────────

@portal_bp.route("/profile", methods=["GET", "POST"])
@login_required
@csrf_required
def profile():
    patient_id = session["patient_id"]
    patient = g.db_manager.get_patient_full(patient_id)
    insurance = g.db_manager.get_patient_insurance(patient_id)
    allergies = g.db_manager.get_patient_allergies(patient_id)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_contact":
            g.db_manager.update_patient(patient_id,
                email=request.form.get("email", "").strip(),
                phone=request.form.get("phone", "").strip(),
                address=request.form.get("address", "").strip(),
                city=request.form.get("city", "").strip(),
                state=request.form.get("state", "").strip(),
                zip_code=request.form.get("zip_code", "").strip()
            )
            flash("Contact information updated.", "success")
            return redirect(url_for("portal.profile"))

    return render_template("profile.html",
        patient=patient, insurance=insurance, allergies=allergies)


# ── API Endpoints ──────────────────────────────────────────────────────────────

@portal_bp.route("/api/prescriptions")
@login_required
def api_prescriptions():
    rxs = g.db_manager.get_prescriptions_by_patient(session["patient_id"])
    return jsonify(rxs)


@portal_bp.route("/api/invoices/outstanding")
@login_required
def api_outstanding():
    invoices = g.db_manager.get_patient_invoices(session["patient_id"])
    outstanding = [i for i in invoices if i["status"] in ("sent", "partial", "overdue")]
    return jsonify(outstanding)


# ── Secure Messages ──────────────────────────────────────────────────────

@portal_bp.route("/messages")
@login_required
def messages():
    patient_id = session["patient_id"]
    threads = g.db_manager.get_message_threads(
        patient_id=patient_id, reader_type="patient")
    return render_template("messages.html",
                           threads=threads, patient_name=session.get("patient_name", ""))


@portal_bp.route("/messages/new", methods=["GET", "POST"])
@login_required
@csrf_required
def new_message():
    patient_id = session["patient_id"]
    providers = g.db_manager.get_providers()
    if request.method == "POST":
        subject = (request.form.get("subject") or "").strip()
        body = (request.form.get("body") or "").strip()
        provider_id = request.form.get("provider_id", type=int)
        if not subject or not body:
            flash("Subject and message are required.", "danger")
            return render_template("message_new.html", providers=providers,
                                   subject=subject, body=body,
                                   patient_name=session.get("patient_name", ""))
        thread_id = g.db_manager.create_message_thread(
            patient_id=patient_id,
            provider_id=provider_id if provider_id else None,
            subject=subject)
        g.db_manager.post_secure_message(
            thread_id=thread_id, sender_type="patient",
            sender_id=session["user_id"], body_plain=body)
        flash("Message sent.", "success")
        return redirect(url_for("portal.message_thread", thread_id=thread_id))
    return render_template("message_new.html", providers=providers,
                           patient_name=session.get("patient_name", ""))


@portal_bp.route("/messages/<int:thread_id>", methods=["GET", "POST"])
@login_required
@csrf_required
def message_thread(thread_id):
    patient_id = session["patient_id"]
    thread = g.db_manager.get_message_thread(thread_id)
    if not thread or thread["patient_id"] != patient_id:
        flash("Message not found.", "danger")
        return redirect(url_for("portal.messages"))
    if request.method == "POST":
        if thread.get("is_closed"):
            flash("This thread is closed.", "warning")
            return redirect(url_for("portal.message_thread", thread_id=thread_id))
        body = (request.form.get("body") or "").strip()
        if not body:
            flash("Message body cannot be empty.", "danger")
            return redirect(url_for("portal.message_thread", thread_id=thread_id))
        g.db_manager.post_secure_message(
            thread_id=thread_id, sender_type="patient",
            sender_id=session["user_id"], body_plain=body)
        return redirect(url_for("portal.message_thread", thread_id=thread_id))
    messages_list = g.db_manager.get_thread_messages(thread_id)
    g.db_manager.mark_messages_read(thread_id, reader_type="patient")
    return render_template("message_thread.html",
                           thread=thread, messages=messages_list,
                           patient_name=session.get("patient_name", ""))


@portal_bp.route("/api/notifications")
@login_required
def api_notifications():
    patient_id = session["patient_id"]
    notifications = []
    invoices = g.db_manager.get_patient_invoices(patient_id)
    for inv in invoices:
        if inv["status"] == "overdue":
            notifications.append({"type": "danger", "message": f"Invoice {inv['invoice_number']} is overdue"})
        elif inv["status"] in ("sent", "partial"):
            notifications.append({"type": "warning", "message": f"Invoice {inv['invoice_number']} has balance ${inv['balance_due']:.2f}"})

    appts = g.db_manager.get_appointments(patient_id=patient_id)
    for a in appts:
        if a["status"] in ("scheduled", "confirmed"):
            notifications.append({"type": "info", "message": f"Upcoming appointment: {a['scheduled_datetime']}"})

    return jsonify({"count": len(notifications), "notifications": notifications[:10]})
