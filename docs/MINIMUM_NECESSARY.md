# Minimum Necessary Standard — Policy

**Regulatory basis:** 45 CFR § 164.502(b) and § 164.514(d).
A covered entity must, when using or disclosing PHI or when
requesting PHI from another entity, make reasonable efforts to limit
the PHI to the **minimum necessary** to accomplish the intended
purpose.

This policy is binding on every workforce member, vendor, and
business associate of {covered_entity_name}.

---

## 1. The principle

The minimum-necessary standard does **not** require the smallest
possible disclosure in absolute terms. It requires the smallest
disclosure consistent with **doing the job well**:

- A clinician evaluating a patient needs the **whole** chart for
  treatment.
- A billing clerk filing a claim needs CPT codes, ICD-10 codes,
  encounter date, payer ID, patient identifiers — **not** the
  free-text clinical notes.
- A scheduling clerk needs name, contact information, and the
  appointment slot — **not** any clinical content.

The standard does **not** apply to disclosures to or requests by a
provider for treatment, to the patient themselves, with the
patient's authorisation, to HHS for enforcement, or as required by
law (45 CFR § 164.502(b)(2)).

## 2. How MedPharm enforces minimum necessary

### 2.1 Role-based access control

Roles in `database/models.UserRole` constrain which screens and
which actions are visible:

| Role | Sees the chart | Edits the chart | Bills | Schedules | Admin |
|------|:--------------:|:---------------:|:-----:|:---------:|:-----:|
| **Doctor / Psychiatrist** | full | yes | read-only | yes | — |
| **Nurse** | full | yes (notes, vitals) | read-only | yes | — |
| **Pharmacist** | medications + allergies + active diagnoses + recent vitals | dispensing only | read-only | — | medications catalogue |
| **Pharmacy Tech** | medications + allergies (read-only) | — | — | — | medications catalogue (read-only) |
| **Receptionist** | demographics + appointment list | demographics | take payments | yes | — |
| **Billing clerk** | CPT/ICD codes, charges, payments | edit charges, payments | yes | — | — |
| **Administrator** | full | yes (with audit) | yes | yes | full |

The role is set at sign-in and re-checked on every protected route
(`@login_required`, role-aware endpoints) and on every clinical
widget in the desktop client.

### 2.2 Field-level controls

Beyond the row-level RBAC, certain field categories carry
extra controls:

| Field category | Control |
|----------------|---------|
| SSN (full / last 4) | Stored encrypted via `security.encryption.FieldCipher`. The full SSN is never displayed; the last-4 is rendered behind a one-click reveal that emits a `phi_access_log` row. |
| Mental-health, substance-use notes | Tagged on the `MedicalRecord` row; only roles with the corresponding right see them; access fires the `phi_access_log` with `reason=TREATMENT` and a flag. |
| Insurance-policy IDs | Encrypted at rest. |
| Free-text notes | Visible to the clinical roles; redacted to billing/scheduling. |

### 2.3 Disclosures to business associates

Vendor accounts (BAA-bound) are constrained by API scope:

- A pharmacy partner endpoint exposes only the prescription-fill
  feed, never the full chart.
- An analytics provider receives **de-identified** data sets via
  `security/deidentify.py` (Safe Harbor § 164.514(b)(2)).
- A claim-submission clearing-house receives only the claim
  payload — codes, charges, identifiers required by HIPAA TCS.

Each vendor's scope is documented in the vendor register and
reviewed annually with the BAA.

### 2.4 Patient-portal disclosures (to the patient themselves)

Disclosures to the patient are explicitly **not** subject to the
minimum-necessary standard (§ 164.502(b)(2)(iii)). The portal
shows the patient their own chart in full, except where the clinic
has elected to suppress provisional results until a clinician has
reviewed them — this is a clinical-quality choice, not a
HIPAA constraint.

## 3. How a workforce member applies the standard day-to-day

- **Open the smallest scope that lets you finish the task.** If you
  are looking up an upcoming appointment, do not also open the
  patient's medical record.
- **Do not browse charts you have no business reason to read.**
  Every read is logged. The audit-log review (§ 5) sees pattern
  reads and triages them.
- **When sharing a record (fax, secure message, print)**, share
  only the part the recipient asked for. A consultant referral
  often does not need the patient's billing history.
- **When teaching**, use the de-identified copy. Where teaching
  requires the real chart, obtain the patient's authorisation in
  writing.
- **When you don't know**, ask the Privacy Officer. There is no
  penalty for the question; there is for the unauthorised
  disclosure.

## 4. Workforce-requested PHI from external sources

When the entity requests PHI from outside (a referring provider, a
payer's medical-management department, etc.), the workforce member
or the system requests the **smallest** payload that accomplishes
the purpose. A blanket "send the whole chart" request is acceptable
only for treatment continuation between two providers, and is
documented as such in the requesting note.

## 5. Audit and enforcement

The Privacy Officer reviews the audit log monthly for patterns
suggestive of over-broad access:

- A workforce member with an unusually wide read pattern relative
  to their role.
- A workforce member reading a record outside their care team or
  outside their normal hours.
- Reads of records belonging to family members, public figures, or
  fellow workforce members (a frequent cause of sanctions).

Any anomaly opens an investigation under
`docs/SANCTIONS_POLICY.md`.

## 6. Updates to this policy

Roles, field categories, and vendor scopes change. The policy is
reviewed annually by the Privacy Officer and the Security Officer,
and re-issued whenever a material change is made. The current
version is published in the staff portal and referenced from the
training material in `docs/WORKFORCE_TRAINING.md`.
