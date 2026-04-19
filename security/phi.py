# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
PHI access logging (§ 164.312(b)).

HIPAA audit controls require logging every access to protected health
information, not merely mutations. The @log_phi_access decorator stamps a
PHIAccessLog row for each successful handler invocation that touches PHI.
"""

import enum
import time
from functools import wraps
from flask import g, request


class PHIAccessReason(enum.Enum):
    TREATMENT = "treatment"
    PAYMENT = "payment"
    OPERATIONS = "operations"
    PATIENT_SELF_SERVICE = "patient_self_service"
    EMERGENCY = "emergency"
    RESEARCH = "research"
    LEGAL = "legal"
    OTHER = "other"


def _client_ip() -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or ""


def log_phi_access(*, entity_type: str, reason: PHIAccessReason,
                   extract_entity_id=None):
    """
    Decorate a Flask handler that reads PHI. `extract_entity_id` is an
    optional callable(kwargs, result) -> int returning the entity id; when
    None we look for common url args (`patient_id`, `id`, etc.).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            started = time.time()
            result = func(*args, **kwargs)
            try:
                db = getattr(g, "db_manager", None)
                if db is None:
                    return result
                if extract_entity_id is not None:
                    entity_id = extract_entity_id(kwargs, result)
                else:
                    entity_id = (
                        kwargs.get("patient_id")
                        or kwargs.get("id")
                        or kwargs.get("rx_id")
                        or kwargs.get("invoice_id")
                        or getattr(g, "current_patient_id", None)
                    )
                actor_id = (
                    getattr(g, "current_user_id", None)
                    or getattr(g, "user_id", None)
                )
                actor_type = getattr(g, "current_user_type", "") or (
                    "patient" if getattr(g, "patient_id", None) else "staff"
                )
                db.log_phi_access(
                    actor_id=actor_id,
                    actor_type=actor_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    reason=reason.value,
                    endpoint=request.endpoint or request.path,
                    method=request.method,
                    ip=_client_ip(),
                    user_agent=request.headers.get("User-Agent", "")[:300],
                    duration_ms=int((time.time() - started) * 1000),
                )
            except Exception:
                # Audit logging must never break the request path; the
                # DatabaseManager layer itself writes a failure marker.
                pass
            return result
        return wrapper
    return decorator
