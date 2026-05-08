# Risk Analysis & Risk Management — Template

**Regulatory basis:** 45 CFR § 164.308(a)(1)(ii)(A) (Risk Analysis)
and § 164.308(a)(1)(ii)(B) (Risk Management).

**This is a working template.** A covered entity must perform an
accurate and thorough assessment of the potential risks and
vulnerabilities to the confidentiality, integrity, and availability of
ePHI it creates, receives, maintains, or transmits — and must
implement security measures sufficient to reduce those risks and
vulnerabilities to a reasonable and appropriate level.

NIST SP 800-66r2 is the authoritative implementation guidance and
should be read alongside this template.

---

## 0. Document control

| Field | Value |
|-------|-------|
| Reviewing entity | {covered_entity_name} |
| MedPharm version | {medpharm_version} |
| Deployment posture | (single host / multi-host / cloud / Kubernetes) |
| Reviewer(s) | {names_and_roles} |
| Review period start | {start_date} |
| Review period end | {end_date} |
| Next review due | {start_date + 12 months} |

> **Cadence.** OCR audit guidance treats annual review as a floor.
> Re-do the risk analysis whenever (a) the deployment changes
> materially (new module, new vendor, new integration), (b) a
> security incident is closed, or (c) regulators publish new guidance
> that materially changes the risk surface.

## 1. Scope

Inventory **every** asset that creates, receives, maintains, or
transmits ePHI:

| Asset | Type | PHI handled | Controls inherited from MedPharm | Local controls |
|-------|------|-------------|-----------------------------------|----------------|
| Cloud REST API host | Server | Yes — full | TLS, JWT, audit log, encryption-at-rest | (Hosting provider) |
| Patient Web Portal | Server | Yes — full | TLS, session cookies, CSRF, lockout | (HTTPS reverse proxy) |
| Qt Desktop (clinical) | Workstation | Yes — full | RBAC, idle timeout | Disk encryption, screen lock, BIOS password |
| Mobile clients (iOS/Android) | Patient device | Yes — own | Keychain / EncryptedSharedPreferences | Device lock screen |
| Database backups | Storage | Yes — full | Encryption-at-rest | Off-site replication, restore tests |
| Audit log archive | Storage | Metadata + actor | Hash chain | Immutable retention |
| Staff workstations (front desk) | Workstation | Browser session only | Same as portal | Disk encryption, screen lock |
| Network printers | Network | Documents in print queue | — | Pull-to-print + secure release |
| Email gateway | Service | Outbound to patients | (none — out of MedPharm scope) | TLS, DLP, gateway antivirus |

Anything that is **not** in this table is **not** authorised to
process PHI for this deployment.

## 2. Threat sources

The threat sources to evaluate are at minimum the categories from
NIST SP 800-30, tailored to the health-care context:

- **External adversaries** — opportunistic ransomware, targeted
  intrusions for data theft, credential-stuffing, supply-chain
  compromise of a vendor.
- **Insiders** — workforce members exceeding their access ("snooping"
  on a celebrity record, accessing an ex-partner's record),
  disgruntled-departure data exfiltration.
- **Workforce error** — misdirected fax / email, lost device, mistaken
  download to an unencrypted USB stick, weak password reuse.
- **Vendor / business associate failure** — cloud-host outage,
  cloud-host breach, encryption-key compromise at a managed-service
  vendor.
- **Natural / environmental** — fire, flood, prolonged power loss,
  loss of Internet at the office.

## 3. Vulnerabilities to evaluate

For each asset in §1, evaluate at minimum the following
vulnerability classes. The MedPharm deployment-checklist in
`docs/HIPAA_COMPLIANCE.md` covers many; this register tracks the
*residual* risk after those controls are in place.

- Authentication weaknesses (weak passwords, no MFA, shared
  accounts).
- Access-control weaknesses (over-broad RBAC, stale accounts,
  missing offboarding).
- Encryption weaknesses (TLS misconfiguration, weak ciphers, missing
  field-level encryption, key management gaps).
- Logging weaknesses (gaps in PHI access log, log retention < 6
  years, no integrity check).
- Patch hygiene (OS, Python, Node, container base image).
- Backup weaknesses (no encryption, no off-site copy, no restore
  testing).
- Physical security (server room, workstations, mobile devices,
  printed documents).
- Vendor management (no signed BAA, no SOC 2, expired BAA).
- Workforce factors (training gaps, sanctions policy not exercised).
- Application bugs (CVEs in dependencies, regressions in CI).

## 4. Risk register

For each (asset × threat × vulnerability) tuple, score
**likelihood** (1–5) and **impact** (1–5), multiply for a raw risk
score, document the controls in place, and assign a
**risk-treatment decision**.

| ID | Asset | Threat | Vulnerability | Likelihood | Impact | Score | Existing controls | Decision | Owner | Due |
|----|-------|--------|---------------|-----------:|-------:|------:|-------------------|---------|-------|-----|
| 001 | Cloud API | External adversary | TLS misconfig | 1 | 5 | 5 | nginx hardened, HSTS preload, monitored | Accept | Sec. Officer | n/a |
| 002 | Cloud API | External adversary | Stolen JWT secret | 2 | 5 | 10 | secret in vault, rotation runbook | Accept | Sec. Officer | n/a |
| 003 | Portal | Insider | Browser shoulder-surf at front desk | 3 | 3 | 9 | screen-lock policy, idle timeout 15 min | Mitigate | Office Mgr | {date} |
| 004 | Backups | Vendor failure | Backup vendor breach | 1 | 5 | 5 | encrypted backup, vendor BAA | Accept | Sec. Officer | n/a |
| 005 | Workforce | Workforce error | Misdirected email | 4 | 4 | 16 | DLP, training, encrypted-mail enforcement | Mitigate | Privacy Officer | {date} |

### Treatment decisions (NIST SP 800-30)

- **Mitigate** — implement an additional control. List the control,
  the owner, and the due date. Risks above a threshold (typically
  ≥ 12) generally cannot be Accepted without Privacy- and
  Security-Officer sign-off.
- **Transfer** — to a vendor (with BAA) or to cyber-liability
  insurance. Document carrier, policy number, sublimits.
- **Avoid** — eliminate the activity (e.g. stop emailing PHI; require
  portal communication only).
- **Accept** — risk is below the threshold and further mitigation is
  not cost-effective. Sign-off required.

## 5. Mapping to the HIPAA Security Rule

After the register is complete, confirm that every required and
addressable specification under § 164.308, § 164.310, § 164.312, and
§ 164.316 has either been implemented or its decision has been
documented (an addressable specification may be deferred only with
written justification). Use the master mapping table in
`docs/HIPAA_COMPLIANCE.md` as the checklist.

## 6. Risk management plan

For each Mitigate / Transfer item in the register, this section
captures the implementation plan:

| Risk ID | Action | Owner | Resources | Target date | Verification |
|---------|--------|-------|-----------|-------------|--------------|
| 003 | Privacy filter on shared monitor; staff training refresher | Office Mgr | n/a | {date} | Quarterly walk-through |
| 005 | Configure mail gateway DLP rule for SSN/MRN; mandatory training module | IT | $X license | {date} | Penetration test of the rule |

## 7. Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Privacy Officer | | | |
| Security Officer | | | |
| Senior Management | | | |

The signed risk-analysis is retained for **six years from the date of
its creation or the date when it was last in effect, whichever is
later** (45 CFR § 164.316(b)(2)(i)).
