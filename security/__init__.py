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
MedPharm Security Package

Implements the HIPAA Security Rule technical safeguards (45 CFR § 164.312):
    - Access control              (a)  -> lockout, sessions, RBAC hooks
    - Audit controls              (b)  -> hash-chained audit log, PHI access log
    - Integrity controls          (c)  -> audit hash chain, encrypted columns
    - Person/entity authentication (d) -> password policy, TOTP MFA
    - Transmission security       (e)  -> Fernet field encryption, TLS helpers

Code alone cannot produce HIPAA compliance. Deployments must also execute
Business Associate Agreements, publish policies, train the workforce, and
run a periodic risk assessment. See docs/HIPAA_COMPLIANCE.md.
"""

from security.config import (
    SecurityConfig,
    load_security_config,
    require_production_secrets,
)
from security.encryption import (
    FieldCipher,
    encrypt_field,
    decrypt_field,
    rotate_key,
)
from security.passwords import (
    PasswordPolicy,
    validate_password,
    PasswordPolicyError,
)
from security.lockout import (
    LockoutTracker,
    AccountLockedError,
)
from security.audit import (
    AuditChain,
    verify_audit_chain,
)
from security.phi import (
    log_phi_access,
    PHIAccessReason,
)
from security.sessions import (
    apply_session_hardening,
    security_headers,
    enforce_idle_timeout,
)
from security.csrf import (
    generate_csrf_token,
    validate_csrf_token,
    csrf_required,
)
from security.totp import (
    generate_totp_secret,
    generate_totp_uri,
    verify_totp_code,
)
from security.emergency import (
    EmergencyAccessGrant,
    log_emergency_access,
)

__all__ = [
    "SecurityConfig",
    "load_security_config",
    "require_production_secrets",
    "FieldCipher",
    "encrypt_field",
    "decrypt_field",
    "rotate_key",
    "PasswordPolicy",
    "validate_password",
    "PasswordPolicyError",
    "LockoutTracker",
    "AccountLockedError",
    "AuditChain",
    "verify_audit_chain",
    "log_phi_access",
    "PHIAccessReason",
    "apply_session_hardening",
    "security_headers",
    "enforce_idle_timeout",
    "generate_csrf_token",
    "validate_csrf_token",
    "csrf_required",
    "generate_totp_secret",
    "generate_totp_uri",
    "verify_totp_code",
    "EmergencyAccessGrant",
    "log_emergency_access",
]
