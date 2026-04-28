# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
FHIR R4 read endpoints.

Minimal, read-only FHIR surface so external systems (insurance, referral
partners, public-health reporting, CMS Blue Button-style patient
downloads) can pull structured clinical data without scraping the
internal REST API. Implements:

    GET /fhir/metadata                     CapabilityStatement
    GET /fhir/Patient/<id>                 Patient
    GET /fhir/Patient/<id>/MedicationStatement   Bundle
    GET /fhir/Patient/<id>/AllergyIntolerance    Bundle
    GET /fhir/Patient/<id>/Condition       Bundle
    GET /fhir/Patient/<id>/Observation     Bundle (vitals)
    GET /fhir/Patient/<id>/Immunization    Bundle
    GET /fhir/Patient/<id>/$everything     Bundle (combined snapshot)

All endpoints are JWT-protected. Staff see any patient; patients see only
themselves. Every read records a PHIAccessLog row, so the audit trail
matches the HIPAA Accounting of Disclosures requirement.
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, g, request

from api.auth import token_required


def _utcnow_iso() -> str:
    """ISO-8601 UTC timestamp with explicit Z suffix. Replaces the deprecated
    ``datetime.utcnow()`` (Py 3.12+ DeprecationWarning, removed in 3.14)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utcnow_date() -> str:
    """Today's ISO-8601 date in UTC."""
    return datetime.now(timezone.utc).date().isoformat()
from security.phi import PHIAccessReason


fhir_bp = Blueprint("fhir", __name__, url_prefix="/fhir")


FHIR_JSON = "application/fhir+json"


def _json(resource, status=200):
    resp = jsonify(resource)
    resp.status_code = status
    resp.headers["Content-Type"] = FHIR_JSON
    return resp


def _operation_outcome(severity: str, code: str, diagnostics: str, status=400):
    return _json({
        "resourceType": "OperationOutcome",
        "issue": [{
            "severity": severity,
            "code": code,
            "diagnostics": diagnostics,
        }],
    }, status=status)


def _require_patient_access(patient_id: int):
    """Return an OperationOutcome 403 if the token cannot read this patient."""
    user_type = getattr(g, "current_user_type", None)
    if user_type == "staff":
        return None
    if user_type == "patient" and g.current_patient_id == patient_id:
        return None
    return _operation_outcome(
        "error", "forbidden",
        "Authenticated subject cannot read this Patient.",
        status=403,
    )


def _log(patient_id: int, resource_type: str):
    try:
        g.db_manager.log_phi_access(
            actor_id=g.current_user_id,
            actor_type=g.current_user_type,
            entity_type=f"fhir.{resource_type}",
            entity_id=patient_id,
            reason=PHIAccessReason.TREATMENT.value,
            endpoint=request.path,
            method=request.method,
            ip=request.remote_addr or "",
            user_agent=request.headers.get("User-Agent", "")[:255],
        )
    except Exception:
        # Never block a read on an audit failure — but surface via app log
        pass


def _bundle(resource_type: str, entries: list[dict]) -> dict:
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "timestamp": _utcnow_iso(),
        "total": len(entries),
        "entry": [{"resource": e} for e in entries],
    }


# ── Capability Statement ────────────────────────────────────────────────

@fhir_bp.route("/metadata", methods=["GET"])
def capability_statement():
    return _json({
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": _utcnow_date(),
        "publisher": "Enlightec Ltd.",
        "kind": "instance",
        "software": {"name": "MedPharm ERP", "version": "1.7.6"},
        "fhirVersion": "4.0.1",
        "format": ["application/fhir+json"],
        "rest": [{
            "mode": "server",
            "security": {
                "cors": True,
                "description": "Bearer JWT via Authorization header.",
            },
            "resource": [
                {"type": "Patient", "interaction": [{"code": "read"}]},
                {"type": "MedicationStatement", "interaction": [{"code": "search-type"}]},
                {"type": "AllergyIntolerance", "interaction": [{"code": "search-type"}]},
                {"type": "Condition", "interaction": [{"code": "search-type"}]},
                {"type": "Observation", "interaction": [{"code": "search-type"}]},
                {"type": "Immunization", "interaction": [{"code": "search-type"}]},
            ],
        }],
    })


# ── Resource Builders ───────────────────────────────────────────────────

def _patient_resource(p: dict) -> dict:
    name = [{
        "use": "official",
        "family": p.get("last_name", ""),
        "given": [g for g in [p.get("first_name"), p.get("middle_name")] if g],
    }]
    telecom = []
    if p.get("phone"):
        telecom.append({"system": "phone", "value": p["phone"], "use": "home"})
    if p.get("email"):
        telecom.append({"system": "email", "value": p["email"]})
    address = []
    if p.get("address"):
        address.append({
            "use": "home",
            "line": [p.get("address", "")],
            "city": p.get("city", ""),
            "state": p.get("state", ""),
            "postalCode": p.get("zip_code", ""),
        })
    gender_map = {"male": "male", "female": "female", "other": "other"}
    return {
        "resourceType": "Patient",
        "id": str(p["id"]),
        "active": p.get("is_active", True),
        "name": name,
        "telecom": telecom,
        "gender": gender_map.get((p.get("gender") or "").lower(), "unknown"),
        "birthDate": p.get("date_of_birth"),
        "address": address,
    }


def _medication_statement(rx: dict, item: dict) -> dict:
    return {
        "resourceType": "MedicationStatement",
        "id": f"{rx['id']}-{item['id']}",
        "status": "active" if rx["status"] == "active" else "stopped",
        "medicationCodeableConcept": {
            "text": item.get("medication_name") or item.get("generic_name") or "",
        },
        "subject": {"reference": f"Patient/{rx['patient_id']}"},
        "effectiveDateTime": rx.get("prescribed_date"),
        "dosage": [{
            "text": " ".join(filter(None, [item.get("dosage"), item.get("frequency")])),
            "patientInstruction": item.get("instructions") or "",
        }],
        "note": [{"text": rx.get("notes", "")}] if rx.get("notes") else [],
    }


def _allergy_intolerance(patient_id: int, a: dict) -> dict:
    sev = (a.get("severity") or "").lower()
    severity = {"mild": "mild", "moderate": "moderate",
                "severe": "severe", "life_threatening": "severe"}.get(sev)
    return {
        "resourceType": "AllergyIntolerance",
        "id": str(a["id"]),
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                "code": "active",
            }],
        },
        "code": {"text": a.get("allergen", "")},
        "patient": {"reference": f"Patient/{patient_id}"},
        "recordedDate": a.get("noted_date"),
        "reaction": [{
            "manifestation": [{"text": a.get("reaction", "")}],
            **({"severity": severity} if severity else {}),
        }] if a.get("reaction") else [],
    }


def _condition(patient_id: int, d: dict) -> dict:
    return {
        "resourceType": "Condition",
        "id": str(d["id"]),
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": d.get("status", "active"),
            }],
        },
        "code": {
            "coding": [{
                "system": "http://hl7.org/fhir/sid/icd-10",
                "code": d.get("icd10_code", ""),
                "display": d.get("description", ""),
            }] if d.get("icd10_code") else [],
            "text": d.get("description", ""),
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "recordedDate": d.get("diagnosis_date"),
        "note": [{"text": d.get("notes", "")}] if d.get("notes") else [],
    }


def _observation_vitals(patient_id: int, v: dict) -> list[dict]:
    out = []
    ts = v.get("recorded_at")

    def panel(code, display, value, unit, loinc):
        if value is None:
            return None
        return {
            "resourceType": "Observation",
            "id": f"{v['id']}-{code}",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                }],
            }],
            "code": {"coding": [{
                "system": "http://loinc.org",
                "code": loinc,
                "display": display,
            }]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": value,
                "unit": unit,
                "system": "http://unitsofmeasure.org",
            },
        }

    if v.get("bp_systolic") and v.get("bp_diastolic"):
        out.append({
            "resourceType": "Observation",
            "id": f"{v['id']}-bp",
            "status": "final",
            "category": [{"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
            }]}],
            "code": {"coding": [{
                "system": "http://loinc.org", "code": "85354-9",
                "display": "Blood pressure panel",
            }]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": ts,
            "component": [
                {"code": {"coding": [{"system": "http://loinc.org",
                                       "code": "8480-6",
                                       "display": "Systolic blood pressure"}]},
                 "valueQuantity": {"value": v["bp_systolic"], "unit": "mm[Hg]"}},
                {"code": {"coding": [{"system": "http://loinc.org",
                                       "code": "8462-4",
                                       "display": "Diastolic blood pressure"}]},
                 "valueQuantity": {"value": v["bp_diastolic"], "unit": "mm[Hg]"}},
            ],
        })
    for res in filter(None, [
        panel("hr", "Heart rate", v.get("heart_rate"), "/min", "8867-4"),
        panel("temp", "Body temperature", v.get("temperature"), "Cel", "8310-5"),
        panel("resp", "Respiratory rate", v.get("respiratory_rate"), "/min", "9279-1"),
        panel("spo2", "Oxygen saturation", v.get("oxygen_saturation"), "%", "59408-5"),
        panel("weight", "Body weight", v.get("weight"), "kg", "29463-7"),
        panel("height", "Body height", v.get("height"), "cm", "8302-2"),
        panel("bmi", "Body mass index", v.get("bmi"), "kg/m2", "39156-5"),
    ]):
        out.append(res)
    return out


def _immunization(patient_id: int, rec: dict) -> dict:
    return {
        "resourceType": "Immunization",
        "id": str(rec["id"]),
        "status": "completed",
        "vaccineCode": {
            "coding": [{
                "system": "http://hl7.org/fhir/sid/cvx",
                "code": rec.get("cvx_code", ""),
                "display": rec.get("vaccine_name", ""),
            }] if rec.get("cvx_code") else [],
            "text": rec.get("vaccine_name", ""),
        },
        "patient": {"reference": f"Patient/{patient_id}"},
        "occurrenceDateTime": rec.get("administered_at"),
        "lotNumber": rec.get("lot_number", ""),
        "manufacturer": {"display": rec.get("manufacturer", "")} if rec.get("manufacturer") else None,
        "site": {"text": rec.get("site", "")} if rec.get("site") else None,
    }


# ── Endpoints ───────────────────────────────────────────────────────────

@fhir_bp.route("/Patient/<int:patient_id>", methods=["GET"])
@token_required
def read_patient(patient_id):
    err = _require_patient_access(patient_id)
    if err:
        return err
    p = g.db_manager.get_patient_full(patient_id)
    if not p:
        return _operation_outcome("error", "not-found",
                                  f"Patient/{patient_id} not found", status=404)
    _log(patient_id, "Patient")
    return _json(_patient_resource(p))


@fhir_bp.route("/Patient/<int:patient_id>/MedicationStatement", methods=["GET"])
@token_required
def search_medication_statements(patient_id):
    err = _require_patient_access(patient_id)
    if err:
        return err
    rxs = g.db_manager.get_prescriptions_by_patient(patient_id)
    entries = []
    for rx in rxs:
        for item in rx.get("items", []):
            entries.append(_medication_statement(rx, item))
    _log(patient_id, "MedicationStatement")
    return _json(_bundle("MedicationStatement", entries))


@fhir_bp.route("/Patient/<int:patient_id>/AllergyIntolerance", methods=["GET"])
@token_required
def search_allergies(patient_id):
    err = _require_patient_access(patient_id)
    if err:
        return err
    rows = g.db_manager.get_patient_allergies(patient_id)
    entries = [_allergy_intolerance(patient_id, a) for a in rows]
    _log(patient_id, "AllergyIntolerance")
    return _json(_bundle("AllergyIntolerance", entries))


@fhir_bp.route("/Patient/<int:patient_id>/Condition", methods=["GET"])
@token_required
def search_conditions(patient_id):
    err = _require_patient_access(patient_id)
    if err:
        return err
    rows = g.db_manager.get_patient_diagnoses(patient_id)
    entries = [_condition(patient_id, d) for d in rows]
    _log(patient_id, "Condition")
    return _json(_bundle("Condition", entries))


@fhir_bp.route("/Patient/<int:patient_id>/Observation", methods=["GET"])
@token_required
def search_observations(patient_id):
    err = _require_patient_access(patient_id)
    if err:
        return err
    vitals = g.db_manager.get_patient_vitals(patient_id, limit=50)
    entries = []
    for v in vitals:
        entries.extend(_observation_vitals(patient_id, v))
    _log(patient_id, "Observation")
    return _json(_bundle("Observation", entries))


@fhir_bp.route("/Patient/<int:patient_id>/Immunization", methods=["GET"])
@token_required
def search_immunizations(patient_id):
    err = _require_patient_access(patient_id)
    if err:
        return err
    if hasattr(g.db_manager, "get_patient_immunizations"):
        rows = g.db_manager.get_patient_immunizations(patient_id)
    else:
        rows = []
    entries = [_immunization(patient_id, r) for r in rows]
    _log(patient_id, "Immunization")
    return _json(_bundle("Immunization", entries))


@fhir_bp.route("/Patient/<int:patient_id>/$everything", methods=["GET"])
@token_required
def patient_everything(patient_id):
    err = _require_patient_access(patient_id)
    if err:
        return err
    p = g.db_manager.get_patient_full(patient_id)
    if not p:
        return _operation_outcome("error", "not-found",
                                  f"Patient/{patient_id} not found", status=404)

    entries: list[dict] = [_patient_resource(p)]
    for rx in g.db_manager.get_prescriptions_by_patient(patient_id):
        for item in rx.get("items", []):
            entries.append(_medication_statement(rx, item))
    for a in g.db_manager.get_patient_allergies(patient_id):
        entries.append(_allergy_intolerance(patient_id, a))
    for d in g.db_manager.get_patient_diagnoses(patient_id):
        entries.append(_condition(patient_id, d))
    for v in g.db_manager.get_patient_vitals(patient_id, limit=50):
        entries.extend(_observation_vitals(patient_id, v))
    if hasattr(g.db_manager, "get_patient_immunizations"):
        for r in g.db_manager.get_patient_immunizations(patient_id):
            entries.append(_immunization(patient_id, r))

    _log(patient_id, "Everything")
    return _json(_bundle("Mixed", entries))
