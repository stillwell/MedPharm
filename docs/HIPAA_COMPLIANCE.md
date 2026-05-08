# MedPharm ERP — HIPAA Compliance Guide

**Version 1.7.6 · 2026**
**Copyright © 2026 Enlightec Ltd. · GPL-3.0-or-later**

MedPharm ERP implements the HIPAA Security Rule's **technical
safeguards** (45 CFR § 164.312) in code. **Full compliance** also
requires the **administrative** (§ 164.308), **physical** (§ 164.310),
and **organisational** (§ 164.314, § 164.316) safeguards, which are
the responsibility of the covered entity or business associate
deploying the software. This guide is the master map: technical
safeguards in code, plus pointers to the policy and operational docs
in this directory that cover the rest.

The guide has seven sections:

1. The control map — every Security Rule standard, what implements it.
2. The deployment checklist (the gate that every production install must pass).
3. Default configuration values and how to override them.
4. The companion documents — the administrative + physical + organisational pieces.
5. Accounting of disclosures and audit-log integrity.
6. Incident response.
7. References.

---

## 1. The control map

### 1.1 Technical Safeguards (§ 164.312)

| § 164.312 Standard                          | Required / Addressable | Implementation in MedPharm |
|---------------------------------------------|------------------------|----------------------------|
| (a)(1) Access control                       | Required               | `security/lockout.py`, `security/sessions.py`, RBAC in `database/models.UserRole`, `@login_required` on every Flask route, JWT scope check in `api/auth.py` |
| (a)(2)(i) Unique user identification        | Required               | `User`/`PortalAccount` tables (unique usernames, internal `id`); shared accounts are forbidden by `docs/MINIMUM_NECESSARY.md` |
| (a)(2)(ii) Emergency access procedure       | Required               | `security/emergency.py`, `EmergencyAccessGrant` (mandatory ≥ 20-char justification, hash-chained audit entry, time-limited grant) |
| (a)(2)(iii) Automatic logoff                | Addressable            | `security.sessions.enforce_idle_timeout` (default 900 s); JWT access-token expiry (default 24 h) and refresh-token rotation in `api/auth.py` |
| (a)(2)(iv) Encryption & decryption (at rest)| Addressable            | `security/encryption.py` Fernet `FieldCipher` for marked PHI columns; production refuses to boot without `cryptography` installed and `MEDPHARM_FIELD_KEY` set; database-level encryption is the deployment's responsibility (LUKS on the volume, pgcrypto, RDS-managed keys, etc.) |
| (b) Audit controls                          | Required               | `security/audit.AuditChain` (hash-chained `audit_log`); `security/phi.log_phi_access` (`phi_access_log` for every read); `failed_logins` table |
| (c)(1) Integrity                            | Required               | `AuditChain.verify` and the standalone `verify_audit_chain()` CLI; field-cipher tag verifies on read |
| (c)(2) Mechanism to authenticate ePHI       | Addressable            | Hash-chained audit confirms ePHI mutations are not tampered after the fact; field-cipher integrity tag confirms ciphertext was not tampered |
| (d) Person or entity authentication         | Required               | `security/passwords.py` (PBKDF2-SHA256 via Werkzeug; complexity, history, rotation); `security/totp.py` (TOTP MFA); `security/lockout.py` (login monitoring) |
| (e)(1) Transmission security                | Required               | TLS by default: `server/nginx/medpharm-tls.conf` (full stack) or gunicorn `--certfile`/`--keyfile` (API-only). HTTP → 301 → HTTPS; HSTS preload. JWT HMAC and CSRF cover application-layer integrity. |
| (e)(2)(i) Integrity controls in transit     | Addressable            | TLS record-layer integrity; JWT HMAC; CSRF tokens on every POST in the portal |
| (e)(2)(ii) Encryption in transit            | Addressable            | TLS 1.2 / 1.3, ECDHE ciphers, `ssl_prefer_server_ciphers on`; HTTP disabled unless `MEDPHARM_TLS_MODE=disable` (development only) |

### 1.2 Administrative Safeguards (§ 164.308) — pointers

| § 164.308 Standard                                | Where to find it |
|---------------------------------------------------|------------------|
| (a)(1)(ii)(A) Risk Analysis                       | `docs/RISK_ANALYSIS_TEMPLATE.md` |
| (a)(1)(ii)(B) Risk Management                     | Risk-management plan section of the same template |
| (a)(1)(ii)(C) Sanctions Policy                    | `docs/SANCTIONS_POLICY.md` |
| (a)(1)(ii)(D) Information system activity review  | Audit-log review described in §5 below |
| (a)(2) Assigned security responsibility           | Privacy Officer + Security Officer named in `docs/NOTICE_OF_PRIVACY_PRACTICES.md` |
| (a)(3) Workforce security                         | Authorisation + supervision + termination in `docs/WORKFORCE_TRAINING.md` and the staff-onboarding chapter of the Service Manual |
| (a)(4) Information access management              | RBAC + minimum-necessary in `docs/MINIMUM_NECESSARY.md` |
| (a)(5) Security awareness and training            | `docs/WORKFORCE_TRAINING.md` |
| (a)(6) Security incident procedures               | `docs/BREACH_NOTIFICATION.md` and §6 below |
| (a)(7) Contingency plan                           | `docs/CONTINGENCY_PLAN.md` |
| (a)(8) Evaluation                                 | Risk-analysis annual-review cycle |
| (b) Business associate contracts                  | `docs/BAA_TEMPLATE.md` |

### 1.3 Physical Safeguards (§ 164.310) — pointers

The physical safeguards are deployment-environment specific. The
covered entity's facility-security plan must cover, at minimum:

| § 164.310 Standard | Locally owned by | Notes |
|---------------------|------------------|-------|
| (a)(1) Facility access controls | Office Manager | Door codes, visitor log, after-hours access policy |
| (a)(2)(i) Contingency operations | Privacy Officer | Linked to `docs/CONTINGENCY_PLAN.md` |
| (a)(2)(ii) Facility security plan | Office Manager | Locks, alarms, camera retention |
| (a)(2)(iii) Access control and validation | Office Manager | Workforce access by role; visitor escort |
| (a)(2)(iv) Maintenance records | Facilities | Repair / hardware-change log |
| (b) Workstation use | Office Manager + IT | Acceptable-use policy; `docs/WORKFORCE_TRAINING.md` §3.2 |
| (c) Workstation security | IT | Disk encryption, screen lock, BIOS password, idle timeout |
| (d)(1) Device & media controls | IT | Disposal per `docs/DATA_RETENTION_POLICY.md` §4 |
| (d)(2)(i) Disposal | IT | Same |
| (d)(2)(ii) Media re-use | IT | Wipe before re-issue |
| (d)(2)(iii) Accountability | IT | Asset register including all PHI-bearing devices |
| (d)(2)(iv) Data backup and storage | IT | `docs/CONTINGENCY_PLAN.md` §2 |

### 1.4 Organisational Requirements (§ 164.314) — pointers

| § 164.314 Standard | Where |
|---------------------|-------|
| (a) Business Associate contracts | `docs/BAA_TEMPLATE.md` |
| (b)(1) Group health-plan requirements | Out of scope for MedPharm itself; document at the plan-sponsor level |

### 1.5 Policies, Procedures, and Documentation (§ 164.316)

This whole `docs/` directory is the documentation. The retention
floor is **six years** from creation or last-in-effect (whichever is
later) — see `docs/DATA_RETENTION_POLICY.md` §2.

---

## 2. Deployment Checklist (run before go-live)

The boot-time validator in `security/config.require_production_secrets`
enforces the **production-secret** subset of this list. The remaining
items are operational and must be confirmed by the Privacy Officer or
Security Officer signing off the go-live record.

### 2.1 Environment

- [ ] `MEDPHARM_ENV=production` exported in the runtime environment.
- [ ] `MEDPHARM_REQUIRE_TLS=1`.
- [ ] `MEDPHARM_TLS_MODE=require` (or an upstream proxy enforcing
      TLS). `auto` is acceptable only when a CA-issued cert is
      pre-staged in `/etc/ssl/medpharm/`; `disable` is **never**
      acceptable in production.
- [ ] `MEDPHARM_REQUIRE_MFA=1` for staff if your policy requires MFA
      for all staff (the workforce-training program defaults to
      requiring it for all roles with PHI access).

### 2.2 Secrets

All four are 32+ byte random values generated with
`python -c "import secrets; print(secrets.token_urlsafe(32))"` (or
`python -m security.encryption generate-key` for the field key).
**Never** commit secrets to git.

- [ ] `MEDPHARM_JWT_SECRET` set.
- [ ] `MEDPHARM_SECRET_KEY` set (Flask session signing).
- [ ] `MEDPHARM_FIELD_KEY` set, stored in a secret manager (AWS
      Secrets Manager, HashiCorp Vault, GCP Secret Manager).
- [ ] `MEDPHARM_FIELD_KEY_LEGACY` populated only during a rotation
      cycle (comma-separated list of retired keys).

### 2.3 Network

- [ ] `MEDPHARM_CORS_ORIGINS` pinned to the real portal / mobile
      origins. `*` is rejected by the production validator.
- [ ] `nginx` loaded from `server/nginx/medpharm-tls.conf` with a
      valid CA-issued certificate (Let's Encrypt, ACM, or corporate
      PKI). Self-signed certificates are for development only.
- [ ] HSTS preload submission filed (https://hstspreload.org/) once
      the certificate has been served stably for 30+ days.
- [ ] Outbound traffic from the application host is firewalled to
      the egress points it actually needs (DB host, secret manager,
      backup target, audit-log archive, telemetry).

### 2.4 Data

- [ ] Database backups encrypted at rest and shipped to off-site
      storage (`docs/CONTINGENCY_PLAN.md` §2).
- [ ] Restore tested at least **monthly** to a clean staging host.
- [ ] PHI fields configured with `FieldCipher` (insurance ID, SSN
      last-4, message bodies in the messaging tables, free-text
      mental-health notes).
- [ ] De-identified analytics (if any) produced via
      `security.deidentify.safe_harbor` and stored in a separate
      schema.

### 2.5 Process

- [ ] **Signed Business Associate Agreement (BAA)** on file with any
      cloud host or vendor who may encounter PHI
      (`docs/BAA_TEMPLATE.md`).
- [ ] **Notice of Privacy Practices** published and acknowledged at
      first contact (`docs/NOTICE_OF_PRIVACY_PRACTICES.md`).
- [ ] **Workforce training** complete for every member with PHI
      access (`docs/WORKFORCE_TRAINING.md`).
- [ ] **Risk analysis** signed off in the last 12 months
      (`docs/RISK_ANALYSIS_TEMPLATE.md`).
- [ ] **Contingency plan** published, with at least one successful
      backup-restore test and one tabletop DR exercise on file
      (`docs/CONTINGENCY_PLAN.md`).
- [ ] **Sanctions policy** published and acknowledged by every
      workforce member (`docs/SANCTIONS_POLICY.md`).
- [ ] **Patient-rights playbook** in front-desk hands
      (`docs/PATIENT_RIGHTS.md`).
- [ ] **Data-retention policy** in operational use, with the
      disposal register active (`docs/DATA_RETENTION_POLICY.md`).
- [ ] **Breach-notification playbook** rehearsed annually
      (`docs/BREACH_NOTIFICATION.md`).

---

## 3. Default Configuration Values

The defaults are tuned for typical clinical deployments. Override
through the listed environment variables.

| Control                              | Default                     | Env override                      |
|--------------------------------------|-----------------------------|-----------------------------------|
| Idle timeout                         | 900 s (15 min)              | `MEDPHARM_IDLE_TIMEOUT`           |
| Absolute session lifetime cap        | 8 × idle (default 2 h)      | `MEDPHARM_ABSOLUTE_SESSION_LIFETIME` |
| Lockout threshold                    | 5 failures / 15 min window  | `MEDPHARM_LOCKOUT_THRESHOLD`      |
| Lockout duration                     | 1800 s (30 min)             | `MEDPHARM_LOCKOUT_DURATION`       |
| API rate limit (per IP / endpoint)   | 60 req / min                | `MEDPHARM_RATE_LIMIT_PER_MIN`     |
| Password min length                  | 12                          | `MEDPHARM_PWD_MIN_LEN`            |
| Password history                     | 5                           | `MEDPHARM_PWD_HISTORY`            |
| Password max age                     | 90 days                     | `MEDPHARM_PWD_MAX_AGE_DAYS`       |
| MFA requirement (staff)              | optional                    | `MEDPHARM_REQUIRE_MFA`            |
| JWT access-token expiry              | 24 h                        | `MEDPHARM_TOKEN_EXPIRY`           |
| JWT refresh-token expiry             | 7 d                         | `MEDPHARM_REFRESH_EXPIRY`         |
| HSTS max-age                         | 1 year + preload            | `MEDPHARM_HSTS_MAX_AGE`           |
| Audit-log retention (live table)     | indefinite                  | (operator runs the archiver)      |
| Backup retention — daily             | 30 d                        | (deployment-side)                 |
| Backup retention — weekly            | 12 mo                       | (deployment-side)                 |
| Backup retention — annual            | 7 years                     | (deployment-side)                 |

---

## 4. Companion Documents

This file is the index. The detailed material lives in the
documents below. They are versioned in the same git repository so
that policy and code drift is visible and reviewable.

| Topic | Document |
|-------|----------|
| Patient-facing notice | [`NOTICE_OF_PRIVACY_PRACTICES.md`](NOTICE_OF_PRIVACY_PRACTICES.md) |
| Risk analysis & management | [`RISK_ANALYSIS_TEMPLATE.md`](RISK_ANALYSIS_TEMPLATE.md) |
| Backup, DR, emergency mode | [`CONTINGENCY_PLAN.md`](CONTINGENCY_PLAN.md) |
| Sanctions for non-compliance | [`SANCTIONS_POLICY.md`](SANCTIONS_POLICY.md) |
| Workforce training & awareness | [`WORKFORCE_TRAINING.md`](WORKFORCE_TRAINING.md) |
| Retention & disposal of records | [`DATA_RETENTION_POLICY.md`](DATA_RETENTION_POLICY.md) |
| Minimum-necessary standard | [`MINIMUM_NECESSARY.md`](MINIMUM_NECESSARY.md) |
| Patient rights operations | [`PATIENT_RIGHTS.md`](PATIENT_RIGHTS.md) |
| Breach notification | [`BREACH_NOTIFICATION.md`](BREACH_NOTIFICATION.md) |
| Business Associate Agreement template | [`BAA_TEMPLATE.md`](BAA_TEMPLATE.md) |
| Service Manual (Volume II) | [`MedPharm_ERP_Service_Manual.pdf`](MedPharm_ERP_Service_Manual.pdf) |
| Developer Manual (Volume III) | [`MedPharm_ERP_Developer_Manual.pdf`](MedPharm_ERP_Developer_Manual.pdf) |

---

## 5. Accounting of disclosures & audit integrity

### 5.1 What is logged

- Every **PHI read** lands in `phi_access_log` (one row per read,
  via the `@log_phi_access` decorator on Flask handlers and the
  equivalent calls in `api/routes.py` and `qt_app/widgets/*`).
- Every **PHI mutation** lands in `audit_log` via `AuditChain.append`.
- Every **failed login** lands in `failed_logins`.
- Every **emergency-access break-glass** lands in `audit_log` with
  action `emergency_access_granted` and a justification field.

### 5.2 Tamper evidence

The audit chain stores `prev_hash` and `row_hash` per row:

    row_hash = SHA256(prev_hash || canonical_json(row))

`security.audit.verify_audit_chain` recomputes the chain and
returns `(ok, last_id, message)`. Any post-hoc modification of an
historical row breaks the chain at that row.

### 5.3 Periodic integrity check

Run as a scheduled task (cron, systemd timer, Kubernetes CronJob):

    python -c "from security.audit import verify_audit_chain; \
               from database.db_manager import DatabaseManager; \
               ok, last, msg = verify_audit_chain(DatabaseManager()); \
               import sys; sys.exit(0 if ok else 2)"

A non-zero exit code is a **security incident** per § 164.308(a)(6)
and triggers the breach-notification playbook
(`docs/BREACH_NOTIFICATION.md`).

### 5.4 Generating the accounting

The patient-rights playbook (`docs/PATIENT_RIGHTS.md` §3) walks
the front desk through the patient-facing process. The data
source is `phi_access_log` filtered to the patient and to the
disclosure types HIPAA requires reporting (excluding TPO and
patient-self-service reads).

---

## 6. Incident response

A short version of the breach-notification playbook for at-the-keyboard
use. The full version is `docs/BREACH_NOTIFICATION.md`.

1. **Contain.** Disable the affected account
   (`is_active=False`); revoke JWT refresh tokens; if a key is
   compromised, run `security.encryption.rotate_key()` on the
   encrypted columns.
2. **Preserve.** Snapshot the database, the audit chain, and the
   relevant logs **before** any remediation that could alter
   them.
3. **Verify.** `verify_audit_chain()` to confirm log integrity.
4. **Assess.** The four-factor risk assessment in
   `docs/BREACH_NOTIFICATION.md` §2.3.
5. **Notify.** Follow the timelines in
   `docs/BREACH_NOTIFICATION.md` §1.
6. **Document.** Incident register row, post-mortem, action items.
   Update the risk-analysis cycle (`docs/RISK_ANALYSIS_TEMPLATE.md`)
   if the root cause was a residual-risk gap.

---

## 7. What MedPharm does **not** do for you

- Draft or sign BAAs with your hosting providers.
- Enforce your data-retention policy beyond the application layer
  (you configure retention in your backup system per
  `docs/DATA_RETENTION_POLICY.md`).
- Train your workforce or maintain your sanctions policy beyond
  the templates here.
- Produce the annual risk analysis required by
  § 164.308(a)(1)(ii)(A) — the template at
  `docs/RISK_ANALYSIS_TEMPLATE.md` is the framework, but the
  analysis itself must be performed.
- Replace a dedicated SIEM. Pipe `nginx` access logs (JSON) and
  application logs to your SIEM of record (Splunk, ELK, Datadog,
  etc.).
- Provide cyber-liability insurance — but the
  contingency-plan and breach-notification timelines are tuned to
  what most carriers require.

---

## 8. References

- HHS Security Rule overview — https://www.hhs.gov/hipaa/for-professionals/security/
- HHS OCR Privacy Rule — https://www.hhs.gov/hipaa/for-professionals/privacy/
- HHS Breach Notification Rule — https://www.hhs.gov/hipaa/for-professionals/breach-notification/
- NIST SP 800-66r2 — Implementing the HIPAA Security Rule
- NIST SP 800-30 — Guide for Conducting Risk Assessments
- NIST SP 800-88 Rev. 1 — Guidelines for Media Sanitisation
- 45 CFR Parts 160 and 164 — the regulation itself
- HHS Office for Civil Rights complaint portal — https://www.hhs.gov/hipaa/filing-a-complaint/
- HHS OCR breach reporting portal — https://ocrportal.hhs.gov/ocr/breach/
