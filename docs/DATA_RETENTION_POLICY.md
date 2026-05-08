# Data Retention & Disposal Policy

**Regulatory basis:**
- 45 CFR § 164.316(b)(2) — HIPAA documentation retention (six years).
- 45 CFR § 164.530(j) — Privacy Rule documentation retention (six
  years).
- State medical-record retention laws (variable, often 7–10 years
  for adults, longer for minors). Apply the **longest applicable**
  period.

This policy covers (a) **what to keep**, (b) **how long to keep
it**, and (c) **how to dispose of it** when retention ends.

---

## 1. Document control

This policy is owned by the Privacy Officer and reviewed annually.
Material changes require sign-off from the Privacy Officer, the
Security Officer, and outside counsel (when state-law thresholds are
implicated). The current policy is published in the staff portal and
linked from the workforce-training material
(`docs/WORKFORCE_TRAINING.md`).

## 2. Retention table

> **Apply the longest period implied by federal law, state law,
> contract, or this policy.** Retention periods below are floors,
> not ceilings, except where flagged with **destroy at**.

### Clinical records

| Record | Retention | Notes |
|--------|-----------|-------|
| Adult patient medical record (chart, prescriptions, results, imaging) | 10 years from last encounter | State-law variable; many states 6–7 years. |
| Minor patient medical record | Until age of majority + 10 years | State-law variable. |
| Mental-health and psychotherapy notes | 10 years from last encounter | Some states require longer. |
| Reproductive-health, substance-use, HIV/STI records | 10 years from last encounter, plus enhanced access controls | 42 CFR Part 2 may apply for substance-use. |
| Immunisation records | Permanently | State immunisation registries also receive copies. |

### Operational and security

| Record | Retention | Notes |
|--------|-----------|-------|
| HIPAA policies and procedures | 6 years from creation **or** date last in effect — whichever is later | § 164.316(b)(2)(i) |
| Risk analyses (`docs/RISK_ANALYSIS_TEMPLATE.md`) | 6 years from creation or last-in-effect | § 164.316(b)(2)(i) |
| Sanctions register | 6 years from disposition | § 164.530(j) |
| Workforce training records | 6 years | § 164.530(j) |
| Business Associate Agreements | 6 years from termination of agreement | § 164.530(j) |
| Notice of Privacy Practices versions | 6 years from each version's "last in effect" date | § 164.530(j) |
| Audit log (`audit_log` + `phi_access_log`) | **6 years minimum**; default deployment retains the live database table indefinitely | Cold-storage immutable copy starts at year 1 |
| Incident records | 6 years from closure | Includes breach-notification packets |
| Patient-rights request records (access, amendment, accounting) | 6 years from disposition | § 164.530(j) |

### Financial and operational

| Record | Retention | Notes |
|--------|-----------|-------|
| Invoices, payments, claims | 7 years | IRS + state tax requirements |
| Insurance-claim correspondence | 7 years | Recovery audits often have a 5-year reach |
| General ledger, audit reports | 7 years | |
| Backups (daily / weekly / annual) | See `docs/CONTINGENCY_PLAN.md` §2 | Encrypted at rest; key destruction terminates retention |

### Patient self-service / communications

| Record | Retention | Notes |
|--------|-----------|-------|
| Secure messages between patient and clinician | Retained as part of the medical record (= clinical retention) | Threads cannot be silently deleted; closure flag preserves the audit trail |
| Portal login activity | 6 years | Linked to PHI access via `phi_access_log` |
| Failed-login records | 1 year (rolling) | Aggregated for security analytics; do not retain failure metadata indefinitely |
| Consent forms (treatment, NPP receipt, photo, marketing opt-in) | Retained as part of the medical record | Scanned originals attached to chart |

### Marketing and analytics (non-PHI)

| Record | Retention | Notes |
|--------|-----------|-------|
| De-identified analytics | Indefinite | Use `security/deidentify.py` Safe Harbor helper before retention |
| Limited Data Sets used for research | Per the Data Use Agreement | Recipient is contractually bound by 45 CFR § 164.514(e) |

## 3. Records on legal hold

A legal hold (litigation, subpoena, regulatory investigation, OCR
audit) **suspends** the retention schedule for the affected records
and prohibits disposal. The Privacy Officer maintains the hold
register. A hold is released only on written instruction from
counsel.

## 4. Destruction methods

Destruction must render the PHI **unusable, unreadable, or
indecipherable** — the same standard used in the Breach
Notification Rule's safe harbor.

| Medium | Approved method |
|--------|-----------------|
| Paper | Cross-cut shred (DIN 66399 P-4 or higher) by a vendor with a current BAA, or an in-office shredder of equivalent rating. Certificate of destruction kept on file. |
| Electronic — file on a current device | Cryptographic erase (overwrite with all-zeroes if the device supports it; ATA Secure Erase for SSDs; NIST SP 800-88 Rev. 1 sanitisation method). |
| Electronic — backup tape / removable | Crypto-shred (destroy the wrapping key); when end-of-life, physical destruction (degauss for tape; shred for SSD/optical). |
| Database row | Soft delete with a tombstone, then hard delete after 30 days unless a legal hold applies. The audit log retains the action; the row's PHI fields are no longer recoverable. |
| Field-level encrypted column | Crypto-shred (rotate the key, retire the legacy key, then drop the legacy entry from the secret manager). |
| Cloud storage object | Provider-side delete plus crypto-shred of the customer-managed key, **and** wait for the provider's confirmed deletion timeline (often 30 days) before treating the record as destroyed. |
| Physical media being returned to a leasing company | Destroy in-house first; do **not** rely on the leasing company's wipe. |

Destruction of any record under this policy is documented in the
disposal register: tracking number, what was destroyed, method,
date, person performing destruction, witness (where required),
certificate-of-destruction file reference.

## 5. Deletion requested by a patient

A patient request to delete records is **not** the same as a
HIPAA-recognised right. The right is to **request restriction**
(§ 164.522) or **amendment** (§ 164.526) — not deletion. Records
required by law to be retained may not be deleted on request. The
front desk routes any such request to the Privacy Officer, who
responds in writing within 30 days, citing the applicable retention
floor.

State residents may have additional rights under state privacy law
(e.g. CCPA for California residents). The Privacy Officer evaluates
those on a case-by-case basis.

## 6. De-identification as an alternative to disposal

PHI that is fully de-identified per 45 CFR § 164.514(b) is no longer
subject to the Privacy Rule and may be retained indefinitely (and
shared without authorisation). Two methods are permitted:

- **Safe Harbor** (§ 164.514(b)(2)) — remove the 18 enumerated
  identifiers and have no actual knowledge that the residual data
  could re-identify the individual. The MedPharm helper
  `security/deidentify.py` implements the redaction.
- **Expert determination** (§ 164.514(b)(1)) — engage a qualified
  expert who certifies, in writing, that the risk of re-identification
  is very small.

De-identified data sets are tagged with the method used and the
date, and live in a separate schema or datastore from PHI.

## 7. Audit & enforcement

The Privacy Officer audits the disposal register annually. Findings
are entered in the next risk-analysis cycle. Failures of the
disposal process are sanctionable under
`docs/SANCTIONS_POLICY.md`.
