# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
Tamper-evident audit chain.

Each audit-log entry includes a cryptographic hash of (prev_hash || row_data).
Any post-hoc modification of a historical record breaks the chain, which
verify_audit_chain() detects.

This implements § 164.312(b) (audit controls) and § 164.312(c)(1) (integrity).
"""

import hashlib
import json
from datetime import datetime


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def compute_row_hash(prev_hash: str, payload: dict) -> str:
    h = hashlib.sha256()
    h.update((prev_hash or "").encode("utf-8"))
    h.update(b"|")
    h.update(_canonical(payload))
    return h.hexdigest()


class AuditChain:
    """
    Thin helper that wraps DatabaseManager to write hash-chained audit rows.
    The chain head (last hash) is cached in memory; the DB is the source of
    truth via the `prev_hash` column on each AuditLog row.
    """

    GENESIS = "0" * 64

    def __init__(self, db_manager):
        self.db = db_manager

    def _last_hash(self, session) -> str:
        from database.models import AuditLog  # local import to avoid cycle at package load
        row = session.query(AuditLog).order_by(AuditLog.id.desc()).first()
        if not row:
            return self.GENESIS
        return getattr(row, "row_hash", None) or self.GENESIS

    def append(self, *, user_id: int | None, action: str,
               entity_type: str = "", entity_id: int | None = None,
               details: dict | None = None, ip: str = "",
               user_agent: str = "") -> str:
        from database.models import AuditLog

        payload = {
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details or {},
            "ip": ip,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
        }
        with self.db.get_session() as session:
            prev_hash = self._last_hash(session)
            row_hash = compute_row_hash(prev_hash, payload)
            row = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details_json=json.dumps(details) if details else None,
                ip_address=ip,
                user_agent=user_agent,
                prev_hash=prev_hash,
                row_hash=row_hash,
                timestamp=datetime.utcnow(),
            )
            session.add(row)
        return row_hash


def verify_audit_chain(db_manager) -> tuple[bool, int, str]:
    """
    Walk the audit log in id order and recompute each row_hash. Returns
    (ok, last_id_checked, message). On the first mismatch, returns
    (False, failing_id, explanation).
    """
    from database.models import AuditLog

    prev_hash = AuditChain.GENESIS
    last_id = 0
    with db_manager.get_session() as session:
        rows = session.query(AuditLog).order_by(AuditLog.id.asc()).all()
        for row in rows:
            last_id = row.id
            payload = {
                "user_id": row.user_id,
                "action": row.action,
                "entity_type": row.entity_type or "",
                "entity_id": row.entity_id,
                "details": json.loads(row.details_json) if row.details_json else {},
                "ip": row.ip_address or "",
                "user_agent": getattr(row, "user_agent", "") or "",
                "timestamp": row.timestamp.isoformat(timespec="seconds") if row.timestamp else "",
            }
            expected = compute_row_hash(prev_hash, payload)
            if row.prev_hash != prev_hash:
                return False, row.id, "prev_hash mismatch — chain broken"
            if row.row_hash != expected:
                return False, row.id, "row_hash mismatch — record tampered"
            prev_hash = row.row_hash
    return True, last_id, "audit chain verified"
