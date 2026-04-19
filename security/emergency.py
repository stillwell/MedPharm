# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
Emergency access procedure ("break-glass").

§ 164.312(a)(2)(ii) requires a way for authorized workforce members to get
to PHI during an emergency. Every use of this path MUST be logged loudly so
a compliance officer can review it after the fact.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmergencyAccessGrant:
    user_id: int
    patient_id: int
    justification: str
    granted_at: datetime
    expires_at: datetime


def log_emergency_access(db_manager, *, user_id: int, patient_id: int,
                         justification: str, expires_minutes: int = 60,
                         ip: str = "", user_agent: str = "") -> EmergencyAccessGrant:
    """
    Record an emergency-access grant and emit the loudest possible audit
    signal. Caller must ensure the workforce member re-authenticated
    recently (e.g. via MFA challenge) before invoking this.
    """
    if not justification or len(justification.strip()) < 20:
        raise ValueError(
            "Emergency access requires a justification of at least 20 "
            "characters describing the clinical situation."
        )
    now = datetime.utcnow()
    expires = now.replace(microsecond=0)
    # Use timedelta without importing at module scope to keep imports tight
    from datetime import timedelta
    expires = now + timedelta(minutes=expires_minutes)

    grant_id = db_manager.create_emergency_access_grant(
        user_id=user_id,
        patient_id=patient_id,
        justification=justification.strip(),
        expires_at=expires,
        ip=ip,
        user_agent=user_agent,
    )

    # Parallel entry in the main audit chain so the grant is tamper-evident.
    from security.audit import AuditChain
    AuditChain(db_manager).append(
        user_id=user_id,
        action="emergency_access_granted",
        entity_type="patient",
        entity_id=patient_id,
        details={
            "grant_id": grant_id,
            "justification": justification.strip(),
            "expires_at": expires.isoformat(),
        },
        ip=ip,
        user_agent=user_agent,
    )
    return EmergencyAccessGrant(
        user_id=user_id,
        patient_id=patient_id,
        justification=justification.strip(),
        granted_at=now,
        expires_at=expires,
    )
