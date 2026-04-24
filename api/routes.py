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
MedPharm ERP - REST API Routes
JSON API endpoints for Android and mobile clients.
"""

from flask import Blueprint, request, jsonify, g, current_app

from api.auth import (
    create_token, decode_token,
    token_required, patient_required, staff_required
)
from security.lockout import LockoutTracker, AccountLockedError

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


_api_lockout: LockoutTracker | None = None


def _api_lockout_tracker() -> LockoutTracker:
    global _api_lockout
    if _api_lockout is None:
        cfg = current_app.config.get("SECURITY_CONFIG")
        if cfg is None:
            _api_lockout = LockoutTracker()
        else:
            _api_lockout = LockoutTracker(
                threshold=cfg.lockout_threshold,
                window_seconds=cfg.lockout_window_seconds,
                lockout_seconds=cfg.lockout_duration_seconds,
            )
    return _api_lockout


def _record_login_attempt(username: str, *, account_type: str,
                          successful: bool) -> None:
    if successful:
        return
    try:
        g.db_manager.record_failed_login(
            username=username, account_type=account_type,
            ip=request.remote_addr or "",
            user_agent=request.headers.get("User-Agent", "")[:255],
            reason="bad_credentials",
        )
    except Exception:
        pass


# ── Health Check ──────────────────────────────────────────────────────────────

@api_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "MedPharm ERP API", "version": "1.7.4", "copyright": "\u00a9 2026 Enlightec Ltd."})


# ── Authentication ────────────────────────────────────────────────────────────

@api_bp.route("/auth/login/patient", methods=["POST"])
def patient_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body required"}), 400
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    tracker = _api_lockout_tracker()
    key = f"api-patient:{username.lower()}"
    try:
        tracker.assert_not_locked(key)
    except AccountLockedError as exc:
        return jsonify({
            "error": "Account temporarily locked",
            "retry_after_seconds": exc.retry_after,
        }), 429

    account = g.db_manager.authenticate_portal(username, password)
    if not account:
        tracker.record_failure(key)
        _record_login_attempt(username, account_type="patient", successful=False)
        return jsonify({"error": "Invalid credentials"}), 401
    tracker.record_success(key)

    patient = g.db_manager.get_portal_patient(account["id"])
    patient_name = patient["full_name"] if patient else username

    access_token = create_token(
        user_type="patient", user_id=account["id"],
        patient_id=account["patient_id"], username=account["username"],
        name=patient_name
    )
    refresh_token = create_token(
        user_type="patient", user_id=account["id"],
        patient_id=account["patient_id"], username=account["username"],
        name=patient_name, is_refresh=True
    )
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": account["id"],
            "patient_id": account["patient_id"],
            "username": account["username"],
            "name": patient_name,
            "type": "patient",
        }
    })


@api_bp.route("/auth/login/staff", methods=["POST"])
def staff_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body required"}), 400
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    tracker = _api_lockout_tracker()
    key = f"api-staff:{username.lower()}"
    try:
        tracker.assert_not_locked(key)
    except AccountLockedError as exc:
        return jsonify({
            "error": "Account temporarily locked",
            "retry_after_seconds": exc.retry_after,
        }), 429

    user = g.db_manager.authenticate_user(username, password)
    if not user:
        tracker.record_failure(key)
        _record_login_attempt(username, account_type="staff", successful=False)
        return jsonify({"error": "Invalid credentials"}), 401
    tracker.record_success(key)

    access_token = create_token(
        user_type="staff", user_id=user.id,
        username=user.username, role=user.role.value,
        name=user.full_name
    )
    refresh_token = create_token(
        user_type="staff", user_id=user.id,
        username=user.username, role=user.role.value,
        name=user.full_name, is_refresh=True
    )
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "name": user.full_name,
            "type": "staff",
        }
    })


@api_bp.route("/auth/refresh", methods=["POST"])
def refresh_token():
    data = request.get_json(silent=True)
    if not data or "refresh_token" not in data:
        return jsonify({"error": "Refresh token required"}), 400

    payload = decode_token(data["refresh_token"])
    if not payload or payload.get("typ") != "refresh":
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    access_token = create_token(
        user_type=payload["user_type"], user_id=payload["user_id"],
        patient_id=payload.get("patient_id"), username=payload.get("username", ""),
        role=payload.get("role", ""), name=payload.get("name", "")
    )
    return jsonify({"access_token": access_token})


@api_bp.route("/auth/register", methods=["POST"])
def patient_register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body required"}), 400

    required = ["first_name", "last_name", "dob", "ssn_last4", "username", "email", "password"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    from security.passwords import validate_password, PasswordPolicy, PasswordPolicyError
    cfg = current_app.config.get("SECURITY_CONFIG")
    policy = PasswordPolicy(min_length=cfg.password_min_length if cfg else 12)
    try:
        validate_password(data["password"], policy=policy, username=data.get("username", ""))
    except PasswordPolicyError as exc:
        return jsonify({"error": f"Password rejected: {exc}"}), 400

    from datetime import date
    try:
        dob = date.fromisoformat(data["dob"])
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    patient_id = g.db_manager.verify_patient_identity(
        data["first_name"].strip(), data["last_name"].strip(),
        dob, data["ssn_last4"].strip()
    )
    if not patient_id:
        return jsonify({"error": "Identity verification failed. Contact the office."}), 400

    try:
        account_id = g.db_manager.create_portal_account(
            patient_id, data["username"].strip(),
            data["password"], data["email"].strip()
        )
        return jsonify({"message": "Account created successfully", "account_id": account_id}), 201
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 400


# ── Patient Dashboard ─────────────────────────────────────────────────────────

@api_bp.route("/patient/dashboard", methods=["GET"])
@patient_required
def patient_dashboard():
    patient_id = g.current_patient_id
    prescriptions = g.db_manager.get_prescriptions_by_patient(patient_id)
    active_rx = [rx for rx in prescriptions if rx["status"] == "active"]
    invoices = g.db_manager.get_patient_invoices(patient_id)
    outstanding = sum(
        inv["balance_due"] for inv in invoices
        if inv["status"] in ("sent", "partial", "overdue")
    )
    appointments = g.db_manager.get_appointments(patient_id=patient_id)
    upcoming = [a for a in appointments if a["status"] in ("scheduled", "confirmed")]

    return jsonify({
        "active_prescriptions": len(active_rx),
        "upcoming_appointments": len(upcoming),
        "outstanding_balance": float(outstanding),
        "recent_prescriptions": active_rx[:5],
        "next_appointments": upcoming[:5],
        "recent_invoices": invoices[:5],
    })


# ── Patient Profile ───────────────────────────────────────────────────────────

@api_bp.route("/patient/profile", methods=["GET"])
@patient_required
def get_patient_profile():
    patient = g.db_manager.get_patient_full(g.current_patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    insurance = g.db_manager.get_patient_insurance(g.current_patient_id)
    allergies = g.db_manager.get_patient_allergies(g.current_patient_id)
    return jsonify({
        "patient": patient,
        "insurance": insurance,
        "allergies": allergies,
    })


@api_bp.route("/patient/profile", methods=["PUT"])
@patient_required
def update_patient_profile():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body required"}), 400
    allowed = ["email", "phone", "address", "city", "state", "zip_code"]
    updates = {k: v.strip() for k, v in data.items() if k in allowed and isinstance(v, str)}
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400
    g.db_manager.update_patient(g.current_patient_id, **updates)
    return jsonify({"message": "Profile updated successfully"})


# ── Prescriptions ─────────────────────────────────────────────────────────────

@api_bp.route("/patient/prescriptions", methods=["GET"])
@patient_required
def patient_prescriptions():
    rxs = g.db_manager.get_prescriptions_by_patient(g.current_patient_id)
    status_filter = request.args.get("status")
    if status_filter:
        rxs = [r for r in rxs if r["status"] == status_filter]
    return jsonify({"prescriptions": rxs})


@api_bp.route("/patient/prescriptions/<int:rx_id>", methods=["GET"])
@patient_required
def patient_prescription_detail(rx_id):
    rx = g.db_manager.get_prescription(rx_id)
    if not rx or rx["patient_id"] != g.current_patient_id:
        return jsonify({"error": "Prescription not found"}), 404
    return jsonify({"prescription": rx})


@api_bp.route("/patient/prescriptions/<int:rx_id>/refill", methods=["POST"])
@patient_required
def patient_request_refill(rx_id):
    rx = g.db_manager.get_prescription(rx_id)
    if not rx or rx["patient_id"] != g.current_patient_id:
        return jsonify({"error": "Prescription not found"}), 404
    refilled = False
    for item in rx.get("items", []):
        if item["refills_remaining"] > 0:
            g.db_manager.refill_prescription_item(item["id"])
            refilled = True
    if refilled:
        return jsonify({"message": "Refill request submitted successfully"})
    return jsonify({"error": "No refills remaining"}), 400


# ── Billing ───────────────────────────────────────────────────────────────────

@api_bp.route("/patient/billing", methods=["GET"])
@patient_required
def patient_billing():
    invoices = g.db_manager.get_patient_invoices(g.current_patient_id)
    payments = g.db_manager.get_payment_history(patient_id=g.current_patient_id)
    outstanding = sum(
        inv["balance_due"] for inv in invoices
        if inv["status"] in ("sent", "partial", "overdue")
    )
    return jsonify({
        "invoices": invoices,
        "payments": payments[:20],
        "outstanding_balance": float(outstanding),
    })


@api_bp.route("/patient/billing/<int:invoice_id>", methods=["GET"])
@patient_required
def patient_invoice_detail(invoice_id):
    inv = g.db_manager.get_invoice(invoice_id)
    if not inv or inv["patient_id"] != g.current_patient_id:
        return jsonify({"error": "Invoice not found"}), 404
    return jsonify({"invoice": inv})


@api_bp.route("/patient/billing/<int:invoice_id>/pay", methods=["POST"])
@patient_required
def patient_pay_invoice(invoice_id):
    inv = g.db_manager.get_invoice(invoice_id)
    if not inv or inv["patient_id"] != g.current_patient_id:
        return jsonify({"error": "Invoice not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body required"}), 400

    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    method = data.get("payment_method", "credit_card")
    if amount <= 0 or amount > inv["balance_due"]:
        return jsonify({"error": "Invalid payment amount"}), 400

    try:
        payment_id = g.db_manager.record_payment(
            invoice_id=invoice_id, amount=amount,
            payment_method=method,
            portal_account_id=g.current_user_id,
            notes="Payment via MedPharm Android app"
        )
        return jsonify({"message": "Payment processed successfully", "payment_id": payment_id})
    except Exception as e:
        return jsonify({"error": f"Payment failed: {str(e)}"}), 400


# ── Medical Records ───────────────────────────────────────────────────────────

@api_bp.route("/patient/records", methods=["GET"])
@patient_required
def patient_records():
    record_type = request.args.get("type")
    records = g.db_manager.get_patient_records(g.current_patient_id, record_type)
    return jsonify({"records": records})


# ── Appointments ──────────────────────────────────────────────────────────────

@api_bp.route("/patient/appointments", methods=["GET"])
@patient_required
def patient_appointments():
    appts = g.db_manager.get_appointments(patient_id=g.current_patient_id)
    status_filter = request.args.get("status")
    if status_filter:
        appts = [a for a in appts if a["status"] == status_filter]
    return jsonify({"appointments": appts})


# ── Medications ───────────────────────────────────────────────────────────────

@api_bp.route("/patient/medications", methods=["GET"])
@patient_required
def patient_medications():
    rxs = g.db_manager.get_prescriptions_by_patient(g.current_patient_id)
    active_meds = []
    for rx in rxs:
        if rx["status"] == "active":
            for item in rx.get("items", []):
                med = g.db_manager.get_medication(item["medication_id"])
                if med:
                    active_meds.append({
                        **item, **med,
                        "prescriber_name": rx["prescriber_name"]
                    })
    return jsonify({"medications": active_meds})


@api_bp.route("/medications/search", methods=["GET"])
@token_required
def search_medications():
    query = request.args.get("q", "")
    drug_class = request.args.get("drug_class", "")
    schedule = request.args.get("schedule", "")
    meds = g.db_manager.search_medications(query=query, drug_class=drug_class, schedule=schedule)
    return jsonify({"medications": meds})


@api_bp.route("/medications/<int:med_id>", methods=["GET"])
@token_required
def get_medication(med_id):
    med = g.db_manager.get_medication(med_id)
    if not med:
        return jsonify({"error": "Medication not found"}), 404
    return jsonify({"medication": med})


# ── Notifications ─────────────────────────────────────────────────────────────

@api_bp.route("/patient/notifications", methods=["GET"])
@patient_required
def patient_notifications():
    patient_id = g.current_patient_id
    notifications = []

    invoices = g.db_manager.get_patient_invoices(patient_id)
    for inv in invoices:
        if inv["status"] == "overdue":
            notifications.append({
                "type": "danger",
                "title": "Overdue Invoice",
                "message": f"Invoice {inv['invoice_number']} is overdue",
                "invoice_id": inv["id"],
            })
        elif inv["status"] in ("sent", "partial"):
            notifications.append({
                "type": "warning",
                "title": "Outstanding Balance",
                "message": f"Invoice {inv['invoice_number']} has balance ${inv['balance_due']:.2f}",
                "invoice_id": inv["id"],
            })

    appts = g.db_manager.get_appointments(patient_id=patient_id)
    for a in appts:
        if a["status"] in ("scheduled", "confirmed"):
            notifications.append({
                "type": "info",
                "title": "Upcoming Appointment",
                "message": f"Appointment on {a['scheduled_datetime']}",
                "appointment_id": a["id"],
            })

    return jsonify({"count": len(notifications), "notifications": notifications[:20]})


# ── Staff Endpoints ───────────────────────────────────────────────────────────

@api_bp.route("/staff/dashboard", methods=["GET"])
@staff_required
def staff_dashboard():
    stats = g.db_manager.get_dashboard_stats()
    recent = g.db_manager.get_recent_activity(limit=10)
    return jsonify({"stats": stats, "recent_activity": recent})


@api_bp.route("/staff/patients", methods=["GET"])
@staff_required
def staff_patients():
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    if query:
        patients = g.db_manager.search_patients(query)
        return jsonify({"patients": patients, "total": len(patients)})
    patients, total = g.db_manager.get_all_patients(page=page)
    return jsonify({"patients": patients, "total": total, "page": page})


@api_bp.route("/staff/patients/<int:patient_id>", methods=["GET"])
@staff_required
def staff_patient_detail(patient_id):
    patient = g.db_manager.get_patient_full(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    vitals = g.db_manager.get_patient_vitals(patient_id)
    records = g.db_manager.get_patient_records(patient_id)
    return jsonify({"patient": patient, "vitals": vitals, "records": records})


@api_bp.route("/staff/appointments", methods=["GET"])
@staff_required
def staff_appointments():
    date_str = request.args.get("date")
    provider_id = request.args.get("provider_id", type=int)
    if date_str:
        from datetime import date as dt_date
        try:
            target_date = dt_date.fromisoformat(date_str)
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400
        appts = g.db_manager.get_todays_appointments(target_date)
    else:
        appts = g.db_manager.get_appointments(provider_id=provider_id)
    return jsonify({"appointments": appts})


@api_bp.route("/staff/prescriptions", methods=["GET"])
@staff_required
def staff_prescriptions():
    patient_id = request.args.get("patient_id", type=int)
    if patient_id:
        rxs = g.db_manager.get_prescriptions_by_patient(patient_id)
    else:
        rxs = []
    return jsonify({"prescriptions": rxs})


@api_bp.route("/staff/analytics/revenue", methods=["GET"])
@staff_required
def staff_revenue():
    revenue = g.db_manager.get_revenue_by_month()
    return jsonify({"revenue": revenue})


@api_bp.route("/staff/analytics/top-medications", methods=["GET"])
@staff_required
def staff_top_medications():
    meds = g.db_manager.get_top_medications()
    return jsonify({"medications": meds})


@api_bp.route("/staff/analytics/demographics", methods=["GET"])
@staff_required
def staff_demographics():
    demographics = g.db_manager.get_patient_demographics()
    return jsonify({"demographics": demographics})


# ── Insurance Claims ──────────────────────────────────────────────────────

@api_bp.route("/patient/insurance/claims", methods=["GET"])
@patient_required
def patient_insurance_claims():
    claims = g.db_manager.get_insurance_claims(patient_id=g.current_patient_id)
    return jsonify({"claims": claims})


@api_bp.route("/patient/insurance/claims", methods=["POST"])
@patient_required
def patient_submit_claim():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body required"}), 400

    required = ["invoice_id", "insurance_id"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    inv = g.db_manager.get_invoice(data["invoice_id"])
    if not inv or inv["patient_id"] != g.current_patient_id:
        return jsonify({"error": "Invoice not found"}), 404

    insurance = g.db_manager.get_patient_insurance(g.current_patient_id)
    ins_ids = [i["id"] for i in insurance]
    if data["insurance_id"] not in ins_ids:
        return jsonify({"error": "Insurance not found for this patient"}), 404

    # Find copay for the selected insurance
    selected_ins = next((i for i in insurance if i["id"] == data["insurance_id"]), None)
    copay = selected_ins["copay_amount"] if selected_ins else 0

    try:
        claim_id = g.db_manager.submit_insurance_claim(
            invoice_id=data["invoice_id"],
            insurance_id=data["insurance_id"],
            patient_id=g.current_patient_id,
            claimed_amount=inv["balance_due"],
            copay_amount=copay,
            notes=data.get("notes", "Submitted via MedPharm mobile app")
        )
        return jsonify({"message": "Insurance claim submitted", "claim_id": claim_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/patient/insurance", methods=["GET"])
@patient_required
def patient_insurance():
    insurance = g.db_manager.get_patient_insurance(g.current_patient_id)
    return jsonify({"insurance": insurance})


@api_bp.route("/staff/insurance/claims", methods=["GET"])
@staff_required
def staff_insurance_claims():
    patient_id = request.args.get("patient_id", type=int)
    claims = g.db_manager.get_insurance_claims(patient_id=patient_id)
    return jsonify({"claims": claims})


@api_bp.route("/staff/insurance/claims/<int:claim_id>/process", methods=["POST"])
@staff_required
def staff_process_claim(claim_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body required"}), 400
    approved = float(data.get("approved_amount", 0))
    copay = float(data.get("copay_amount", 0))
    deductible = float(data.get("deductible", 0))
    result = g.db_manager.process_insurance_payment(claim_id, approved, copay, deductible)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


# ── Symptoms & Conditions Reference ──────────────────────────────────────

@api_bp.route("/reference/symptoms", methods=["GET"])
@token_required
def search_symptoms():
    query = request.args.get("q", "")
    body_system = request.args.get("body_system", "")
    symptoms = g.db_manager.search_symptoms(query=query, body_system=body_system)
    return jsonify({"symptoms": symptoms})


@api_bp.route("/reference/symptoms/body-systems", methods=["GET"])
@token_required
def get_body_systems():
    systems = g.db_manager.get_all_body_systems()
    return jsonify({"body_systems": systems})


@api_bp.route("/reference/conditions", methods=["GET"])
@token_required
def search_conditions():
    query = request.args.get("q", "")
    category = request.args.get("category", "")
    conditions = g.db_manager.search_conditions(query=query, category=category)
    return jsonify({"conditions": conditions})


@api_bp.route("/reference/conditions/categories", methods=["GET"])
@token_required
def get_condition_categories():
    categories = g.db_manager.get_all_condition_categories()
    return jsonify({"categories": categories})
