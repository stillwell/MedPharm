# MedPharm ERP — Security Policy

**Version 1.7.6 · 2026**

## Reporting a vulnerability

Please report suspected security issues **privately** to
**security@enlightec.com** (PGP key on request). Do not open public
GitHub issues for suspected vulnerabilities.

We will acknowledge receipt within **2 business days** and give you a
more detailed update within **10 business days**. We ask that you:

- Give us a reasonable window to patch before public disclosure (90
  days is the default; we will negotiate a shorter window for
  actively-exploited issues).
- Avoid testing against production deployments you do not own; use the
  installer's `--fresh` option to build a local instance.
- Never access, download, modify, or delete PHI belonging to a
  production user while researching a vulnerability.

## Scope

In scope:

- MedPharm ERP (this repository) — server, API, web portal, desktop/Qt
  application, mobile clients (Android / iOS), installer, and
  uninstaller.
- The Docker Hub images `enlightec/medpharm-api` and
  `enlightec/medpharm-server`.

Out of scope (please coordinate with the operator directly):

- Third-party deployments of MedPharm (report to the covered entity).
- Social-engineering attacks against Enlightec staff.
- Denial-of-service testing against any production endpoint.

## Supported versions

The current **minor release** and the previous minor receive security
fixes. Older versions will be patched only for critical issues.

## Cryptography

- Passwords: PBKDF2-HMAC-SHA256, 600 000 rounds (werkzeug).
- PHI field-level encryption: Fernet (AES-128-CBC + HMAC-SHA256). The
  module ships an in-tree HMAC+XOR fallback for development, but
  production refuses to boot without the `cryptography` package
  installed (and refuses to boot without `MEDPHARM_FIELD_KEY` set).
  Keys are rotated through `security.encryption.rotate_key`; legacy
  keys go in `MEDPHARM_FIELD_KEY_LEGACY` so old ciphertext stays
  readable through the cutover.
- API tokens: HMAC-SHA256-signed JWT-like tokens.
- Transport: TLS 1.2+ enforced at nginx (`server/nginx/medpharm-tls.conf`).

## HIPAA

Technical safeguards and deployment checklist are documented in
[`docs/HIPAA_COMPLIANCE.md`](docs/HIPAA_COMPLIANCE.md). The companion
documents cover the administrative + physical + organisational
safeguards:

- [`docs/NOTICE_OF_PRIVACY_PRACTICES.md`](docs/NOTICE_OF_PRIVACY_PRACTICES.md) — patient-facing notice template (§ 164.520)
- [`docs/RISK_ANALYSIS_TEMPLATE.md`](docs/RISK_ANALYSIS_TEMPLATE.md) — risk analysis & risk-management plan (§ 164.308(a)(1)(ii)(A)–(B))
- [`docs/CONTINGENCY_PLAN.md`](docs/CONTINGENCY_PLAN.md) — backup, DR, and emergency-mode operation (§ 164.308(a)(7))
- [`docs/SANCTIONS_POLICY.md`](docs/SANCTIONS_POLICY.md) — workforce sanctions (§ 164.308(a)(1)(ii)(C))
- [`docs/WORKFORCE_TRAINING.md`](docs/WORKFORCE_TRAINING.md) — security awareness program (§ 164.308(a)(5))
- [`docs/MINIMUM_NECESSARY.md`](docs/MINIMUM_NECESSARY.md) — minimum-necessary policy (§ 164.502(b))
- [`docs/PATIENT_RIGHTS.md`](docs/PATIENT_RIGHTS.md) — access, amendment, accounting, restriction (§§ 164.522–528)
- [`docs/DATA_RETENTION_POLICY.md`](docs/DATA_RETENTION_POLICY.md) — retention & disposal
- [`docs/BAA_TEMPLATE.md`](docs/BAA_TEMPLATE.md) — Business Associate Agreement template
- [`docs/BREACH_NOTIFICATION.md`](docs/BREACH_NOTIFICATION.md) — breach-notification playbook (§§ 164.400–414)

## Secure defaults

- Production `create_cloud_app` / `create_app` refuse to use built-in
  default JWT or field-encryption keys and log an error if they are
  left in place.
- `security.encryption._singleton` aborts production boot if the
  `cryptography` package is missing **or** `MEDPHARM_FIELD_KEY` is
  unset.
- Sessions idle-time-out after 15 minutes by default and have an
  absolute lifetime cap (default 8 × idle = 2 h), configurable via
  `MEDPHARM_ABSOLUTE_SESSION_LIFETIME`.
- Failed-login lockout: 5 attempts per 15-minute window → 30-minute
  lockout (`security.lockout`).
- Sliding-window rate limit: 60 req/min/IP by default
  (`security.rate_limit.RateLimiter`), tunable via
  `MEDPHARM_RATE_LIMIT_PER_MIN`. Apply via the
  `flask_rate_limit` decorator on hot or unauthenticated endpoints.
- CSRF tokens required on all state-changing web routes.
- CSP, HSTS, `X-Frame-Options: DENY`, and `SameSite=Lax` cookies
  applied automatically in the Flask app factories and at the nginx
  edge. Stricter CSP (no `'unsafe-inline'` for scripts) is opt-in via
  `MEDPHARM_STRICT_CSP=1`.
- PHI redaction logging filter (`security.log_redaction`) scrubs SSN,
  phone, email, IP, URL, dates, MRN, ages > 89, and JWTs from log
  records. Install once at process start with
  `install_phi_redaction_filter(logging.getLogger())`.
- Safe Harbor de-identification helper
  (`security.deidentify.safe_harbor`) for analytics export per
  45 CFR § 164.514(b)(2).

## Dependency review

Dependencies are pinned in `requirements.txt`, `requirements-cloud.txt`,
and `requirements-server.txt`. We run `pip-audit` against these on
every release.
