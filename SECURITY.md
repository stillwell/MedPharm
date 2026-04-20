# MedPharm ERP — Security Policy

**Version 1.7.2 · 2026**

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
- PHI field-level encryption: Fernet (AES-128-CBC + HMAC-SHA256),
  falling back to an in-tree HMAC+XOR construction when the
  `cryptography` package is unavailable. Keys must be rotated per
  policy.
- API tokens: HMAC-SHA256-signed JWT-like tokens.
- Transport: TLS 1.2+ enforced at nginx (`server/nginx/medpharm-tls.conf`).

## HIPAA

Technical safeguards and deployment checklist are documented in
`docs/HIPAA_COMPLIANCE.md`. A Business Associate Agreement template is
at `docs/BAA_TEMPLATE.md` and the breach-notification playbook at
`docs/BREACH_NOTIFICATION.md`.

## Secure defaults

- Production `create_cloud_app` / `create_app` refuse to use built-in
  default JWT or field-encryption keys and log an error if they are
  left in place.
- Sessions idle-time-out after 15 minutes by default.
- Failed-login lockout: 5 attempts per 15-minute window → 30-minute
  lockout.
- CSRF tokens required on all state-changing web routes.
- CSP, HSTS, `X-Frame-Options: DENY`, and `SameSite=Lax` cookies
  applied automatically in the Flask app factories and at the nginx
  edge.

## Dependency review

Dependencies are pinned in `requirements.txt`, `requirements-cloud.txt`,
and `requirements-server.txt`. We run `pip-audit` against these on
every release.
