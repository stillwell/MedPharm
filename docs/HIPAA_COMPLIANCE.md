# MedPharm ERP — HIPAA Compliance Guide

**Version 1.7.2 · 2026**
**Copyright © 2026 Enlightec Ltd. · GPL-3.0-or-later**

MedPharm ERP implements the HIPAA Security Rule's **technical safeguards**
(45 CFR § 164.312) in code. Full compliance also requires the
**administrative** (§ 164.308) and **physical** (§ 164.310) safeguards
which are the responsibility of the covered entity or business
associate deploying the software.

This guide maps the Security Rule standards to the MedPharm modules and
controls that satisfy them, and documents the deployment checklist every
production install must complete.

---

## 1. Technical Safeguards — Where the code lives

| § 164.312 Standard                        | Implementation (code)                                |
|-------------------------------------------|------------------------------------------------------|
| (a)(1) Access control                     | `security/lockout.py`, `security/sessions.py`, RBAC in `database/models.UserRole` |
| (a)(2)(i) Unique user identification      | `User`/`PortalAccount` tables (unique usernames)     |
| (a)(2)(ii) Emergency access procedure     | `security/emergency.py`, `EmergencyAccessGrantRec`   |
| (a)(2)(iii) Automatic logoff              | `security.sessions.enforce_idle_timeout` (default 15 min) |
| (a)(2)(iv) Encryption & decryption        | `security/encryption.py` (Fernet for PHI fields)     |
| (b) Audit controls                        | `security/audit.AuditChain` (hash-chained AuditLog)  |
| (c)(1) Integrity                          | `AuditChain`, `verify_audit_chain()`                 |
| (c)(2) Mechanism to authenticate PHI      | `security/audit.verify_audit_chain`                  |
| (d) Person or entity authentication       | `security/passwords.py`, `security/totp.py` (TOTP MFA) |
| (e)(1) Transmission security              | `server/nginx/medpharm-tls.conf` (TLS 1.2+, HSTS)    |
| (e)(2)(i) Integrity controls in transit   | TLS integrity + JWT HMAC in `api/auth.py`            |
| (e)(2)(ii) Encryption in transit          | TLS 1.2+ enforced by nginx                           |

## 2. Accounting of Disclosures — § 164.528

Every PHI read/write is appended to `phi_access_log`. The `AuditChain`
on the main audit table adds tamper-evident hash chaining:

    row_hash = SHA256(prev_hash || canonical_json(row))

Run a periodic integrity check:

    python -c "from security.audit import verify_audit_chain; \
               from database.db_manager import DatabaseManager; \
               ok, last, msg = verify_audit_chain(DatabaseManager()); \
               print(ok, last, msg)"

A failing verification is a **security incident** per § 164.308(a)(6) and
must be documented in the incident register.

## 3. Deployment Checklist (run before go-live)

- [ ] Signed **Business Associate Agreement (BAA)** on file with any cloud
      host or vendor who may encounter PHI. See `docs/BAA_TEMPLATE.md`.
- [ ] `MEDPHARM_ENV=production` exported in the runtime environment.
- [ ] `MEDPHARM_JWT_SECRET` set to a 32+ byte random value.
- [ ] `MEDPHARM_SECRET_KEY` set to a distinct 32+ byte random value.
- [ ] `MEDPHARM_FIELD_KEY` set (generate with
      `python -m security.encryption generate-key`). Store in a secret
      manager (AWS Secrets Manager, HashiCorp Vault, etc.); **never**
      commit it to git.
- [ ] `MEDPHARM_CORS_ORIGINS` pinned to the real portal / mobile origins.
      `*` is rejected by the production validator.
- [ ] `MEDPHARM_REQUIRE_TLS=1`.
- [ ] `MEDPHARM_REQUIRE_MFA=1` if your policy requires MFA for all staff.
- [ ] `nginx` loaded from `server/nginx/medpharm-tls.conf` with a valid
      CA-issued certificate (Let's Encrypt, ACM, or corporate PKI).
      Self-signed certificates are for development only.
- [ ] Database backups encrypted at rest and tested monthly.
- [ ] Workforce security-awareness training on file (§ 164.308(a)(5)).
- [ ] Contingency plan (backup, disaster recovery, emergency mode, testing)
      documented and exercised annually (§ 164.308(a)(7)).
- [ ] Risk analysis and risk-management plan reviewed annually
      (§ 164.308(a)(1)).

## 4. Default Configuration Values

| Control                         | Default                     | Env override                      |
|---------------------------------|-----------------------------|-----------------------------------|
| Idle timeout                    | 900 s (15 min)              | `MEDPHARM_IDLE_TIMEOUT`           |
| Lockout threshold               | 5 failures / 15 min window  | `MEDPHARM_LOCKOUT_THRESHOLD`      |
| Lockout duration                | 1800 s (30 min)             | `MEDPHARM_LOCKOUT_DURATION`       |
| Password min length             | 12                          | `MEDPHARM_PWD_MIN_LEN`            |
| Password history                | 5                           | `MEDPHARM_PWD_HISTORY`            |
| Password max age                | 90 days                     | `MEDPHARM_PWD_MAX_AGE_DAYS`       |
| JWT access expiry               | 24 h                        | `MEDPHARM_TOKEN_EXPIRY`           |
| Refresh token expiry            | 7 d                         | `MEDPHARM_REFRESH_EXPIRY`         |
| HSTS max-age                    | 1 year + preload            | `MEDPHARM_HSTS_MAX_AGE`           |

## 5. What MedPharm does **not** do for you

- Draft or sign BAAs with your hosting providers.
- Enforce your data-retention policy (you configure retention in your
  backup system).
- Train your workforce or maintain your sanctions policy.
- Produce the annual risk analysis required by § 164.308(a)(1)(ii)(A).
- Replace a dedicated SIEM. Pipe `nginx` access logs (JSON) and
  application logs to your SIEM of record (Splunk, ELK, Datadog, etc.).

## 6. Incident response

1. Contain — disable the affected account via the Admin UI or by setting
   `is_active=False` on the user record.
2. Preserve — snapshot the database and audit chain before any
   remediation that might alter it.
3. Verify the audit chain integrity (`verify_audit_chain`).
4. Notify — follow `docs/BREACH_NOTIFICATION.md`, which captures the
   § 164.404 / § 164.406 / § 164.408 notice timelines.
5. Document in the incident register and close out with a post-mortem.

## 7. References

- HHS Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/
- NIST SP 800-66r2 (HIPAA Security Rule implementation guidance)
- 45 CFR Parts 160 and 164
