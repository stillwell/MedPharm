# Breach Notification Playbook

**Regulatory basis:** 45 CFR §§ 164.400–414 (HITECH Breach Notification
Rule). This is an operational playbook; it does not substitute for
legal counsel.

---

## 0. Definitions (HIPAA § 164.402)

A **breach** is the acquisition, access, use, or disclosure of PHI in a
manner not permitted by the Privacy Rule, which compromises the
security or privacy of that PHI — unless a **risk assessment** (below)
concludes a low probability of compromise.

An event is **not** a breach if:

1. Unintentional acquisition by a workforce member acting in good faith
   within the scope of authority and no further use/disclosure occurred.
2. Inadvertent disclosure between two authorized persons at the same
   entity and no further use/disclosure occurred.
3. The recipient could not reasonably have retained the PHI.
4. The PHI was rendered unusable, unreadable, or indecipherable under
   the HHS guidance (essentially, **encryption** via FIPS 140-compliant
   means, or destruction).

## 1. Timeline (§ 164.404, § 164.406, § 164.408)

| Step | Who                      | When                                   |
|-----:|--------------------------|----------------------------------------|
| 1    | Discovery logged         | T0 (day of discovery)                  |
| 2    | Contain + preserve       | T0 + 24 h                              |
| 3    | Risk assessment complete | T0 + 5 business days                   |
| 4    | Notify each individual   | Without unreasonable delay, no later than **60 calendar days** after discovery |
| 5    | Notify HHS (< 500)       | Within **60 days of end of calendar year** via the HHS web form |
| 5b   | Notify HHS (≥ 500)       | Without unreasonable delay, no later than **60 calendar days** |
| 6    | Media notice (≥ 500)     | Prominent media in affected state / jurisdiction, **60 days** |

**State law** may require faster notification (e.g. some state laws
require 30 days). Always apply the **shortest applicable** timeline.

## 2. On-call workflow

### Stage 1 — Triage (first hour)

- Identify the affected systems, records, and approximate patient
  count.
- Pull the relevant window from `audit_log` and `phi_access_log`.
- Run `verify_audit_chain` to confirm log integrity.
- Open an incident ticket and a secure incident channel.

### Stage 2 — Containment (first 24 h)

- Revoke the compromised credentials or API keys.
- Rotate `MEDPHARM_JWT_SECRET`, `MEDPHARM_SECRET_KEY`, and if field
  encryption keys are suspected compromised, run
  `security.encryption.rotate_key()` on the encrypted columns.
- Snapshot databases and logs for forensics.

### Stage 3 — Risk assessment (§ 164.402(2))

Four-factor analysis, documented in the incident record:

1. **Nature and extent** of PHI involved (identifiers, sensitive
   categories such as mental-health, substance-use, HIV/STI).
2. The **unauthorized person** who used the PHI or to whom it was
   disclosed.
3. Whether the PHI was **actually acquired or viewed**.
4. The extent to which the risk has been **mitigated**.

A **low probability** outcome must be justified in writing; otherwise
proceed to notification.

### Stage 4 — Notification

- **Individual notice** — first-class mail (or email if the individual
  has consented). Must include: a brief description, types of PHI
  involved, steps the individual should take, what you are doing, and
  contact information.
- **Substitute notice** — if contact information for ≥ 10 individuals
  is insufficient, post on the home page for 90 days **or** major-print
  / broadcast media, with a toll-free number active 90 days.
- **HHS notice** — https://ocrportal.hhs.gov/ocr/breach/
- **Media notice** — for breaches of > 500 in a state or jurisdiction.

### Stage 5 — Post-incident

- Post-mortem within 10 business days.
- Update risk analysis and risk-management plan.
- Update workforce training as needed.
- Close ticket with all artifacts linked.

## 3. Contacts (fill in for your deployment)

- Privacy Officer: **{privacy_officer_name_and_phone}**
- Security Officer: **{security_officer_name_and_phone}**
- Outside counsel: **{counsel_name_and_phone}**
- Cyber-liability carrier incident hotline: **{insurer_hotline}**
- Public-relations firm: **{pr_firm_contact}**

## 4. Templates

See `docs/BAA_TEMPLATE.md` for the Business Associate Agreement
template. Individual breach-notice letter templates are maintained in
your compliance folder and should be kept current with the most recent
HHS guidance.
