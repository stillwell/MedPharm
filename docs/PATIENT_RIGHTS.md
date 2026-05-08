# Patient Rights — Operations Playbook

**Regulatory basis:** 45 CFR §§ 164.522–164.528 (Privacy Rule) and
the corresponding requirements at the state level. Apply the
**most patient-favourable** of federal and state requirements.

This is the playbook the front desk and Privacy Officer follow
when a patient asserts a right. The patient-facing description of
these rights lives in `docs/NOTICE_OF_PRIVACY_PRACTICES.md`.

---

## 0. General principles

- Every right-of-the-patient request is **routed to the Privacy
  Officer** the same business day. Front desk does not respond
  substantively.
- The Privacy Officer opens a tracking record (a row in the
  `patient_rights_request` register). The tracking number is the
  reference for all subsequent correspondence.
- **Identity verification.** Before disclosing PHI to the patient
  or their personal representative, verify identity. Acceptable
  forms: government-issued photo ID; a portal sign-in plus
  knowledge factor (date of birth + last 4 of SSN); a notarised
  authorisation for a personal representative; a court order
  appointing a guardian. Document the method in the request
  record.
- A request from a **personal representative** (parent of a minor,
  guardian, executor) is honoured to the same extent as a request
  from the patient — but only within the scope of the
  representative's authority. State law may further restrict (for
  example, an adolescent's reproductive-health record).
- **Fees** are cost-based and disclosed in writing **before** the
  patient incurs them (§ 164.524(c)(4)). Fees may include the cost
  of supplies, postage, and a reasonable amount of staff time for
  copying. Search-and-retrieval time is **not** a permissible fee
  component for the right of access.

## 1. Right of access (§ 164.524)

A patient may request a copy of their PHI in a "designated record
set". MedPharm treats the **medical record + billing record** as
the designated record set.

### 1.1 Format

The patient chooses the format if MedPharm can readily produce it:

- Through the **patient portal** — instant, free, log every access
  in `phi_access_log`.
- A **direct download** from the portal in PDF or CSV — instant,
  free.
- A **summary** — must be agreed in writing.
- **Paper** — fee-based; must be ready within the response timeline
  (§1.2).
- A **machine-readable export** (HL7 FHIR R4 — see `api/fhir.py`) —
  routed to the patient's chosen target. The patient must
  authorise the target in writing; the authorisation captures the
  target endpoint, the format, and the scope.

### 1.2 Timeline

| Event | Deadline |
|-------|----------|
| Acknowledgement of request | 5 business days |
| Disclosure | **30 calendar days** from receipt of request |
| Extension (one only, with written notice) | +30 calendar days |
| State law may shorten | apply the shortest applicable |

A request from a patient who already uses the portal is fulfilled
in real time by a click; the timeline is for the **paper** path
and for the FHIR-export path.

### 1.3 Denial

The right of access is denied only in narrow circumstances
(§ 164.524(a)(2)–(3)):

- The information is **psychotherapy notes**.
- The information is compiled in reasonable anticipation of a
  legal proceeding.
- A licensed health-care professional has determined that access
  is reasonably likely to **endanger** the patient or another
  person.

A denial is in writing, cites the specific basis, and provides a
review path (the patient may request review by another licensed
professional not involved in the original denial).

### 1.4 Procedure

1. Front desk hands the patient a request form; or the request
   arrives by mail / portal / phone.
2. Privacy Officer logs the tracking record.
3. Identity is verified.
4. Privacy Officer determines scope (full chart? a date range? a
   specific document?).
5. Records are pulled — for the database, via the read-only export
   in `database/db_manager.export_patient_record(patient_id)`.
6. PHI of other patients (e.g. in a co-mingled note) is **redacted
   or removed**. Other-patient data is never disclosed.
7. The records and a cover letter are sent in the chosen format.
8. The disclosure is recorded in `phi_access_log` with
   `reason=PATIENT_SELF_SERVICE` (or `LEGAL` if it is a legal
   request from the patient).
9. The tracking record is closed when the patient confirms receipt
   or when the disclosure is documented as sent.

## 2. Right to amend (§ 164.526)

A patient may request that we amend incorrect or incomplete PHI in
the designated record set.

### 2.1 Timeline

- Acknowledgement: 5 business days.
- Decision: **60 calendar days** of receipt; one 30-day extension
  with written notice.

### 2.2 Decision

We may **deny** an amendment when the PHI:

- Was not created by us (and the originator is available to amend
  it).
- Is not part of the designated record set.
- Would not be available for inspection under the right of access
  (§1.3).
- Is accurate and complete.

A denial is in writing, cites the basis, and tells the patient
they may submit a **statement of disagreement**, which we attach
to the record and disclose with future disclosures of the
disputed PHI.

### 2.3 Implementation

When an amendment is granted:

1. The original entry is **never overwritten**. Instead, the
   correction is stored as a new entry in
   `MedicalRecordAmendment`, linked to the original.
2. Both the original and the amendment are visible together; the
   original is flagged as superseded.
3. We notify, where reasonable, the persons identified by the
   patient as having received the disputed PHI.

## 3. Accounting of disclosures (§ 164.528)

A patient may request a list of disclosures we have made of their
PHI, going back **six years** before the request date (or shorter
if the relationship is shorter).

### 3.1 What is included

- Disclosures to public-health authorities, law enforcement, the
  coroner, and similar.
- Disclosures **required by law**.
- Health-oversight disclosures (excluding payment-fraud
  investigations of the patient).
- Judicial / administrative-proceeding disclosures.
- Workers'-compensation disclosures.
- Disclosures to family members the patient identified.
- Breach disclosures.

### 3.2 What is excluded

- Disclosures to carry out treatment, payment, and operations.
- Disclosures to the patient themselves.
- Disclosures the patient authorised.
- Disclosures incidental to a permitted use.
- Disclosures for facility directories.
- Limited Data Set disclosures.

### 3.3 Source of the data

The MedPharm `phi_access_log` table records every read; the
`audit_log` records every write. The accounting is generated by
filtering both tables on `entity_type='patient'` and
`entity_id={patient_id}`, narrowing to the included reasons, and
formatting per § 164.528(b).

### 3.4 Timeline and fee

- Acknowledgement: 5 business days.
- Disclosure: **60 calendar days** of receipt; one 30-day
  extension with written notice.
- The first accounting in any 12-month period is **free**;
  additional accountings within the same period may be
  cost-based, with a written cost estimate before the work
  begins.

## 4. Right to request restriction (§ 164.522(a))

A patient may request that we restrict certain uses or disclosures
of their PHI for treatment, payment, or health-care operations.

We are **not required** to agree to the restriction, **except**
when the patient asks us to refrain from disclosing PHI to a
**health plan** for a service the patient has paid for **in full
out of pocket**. That restriction we **must** honour.

### 4.1 Procedure

1. Privacy Officer logs the request and confirms the scope in
   writing.
2. A flag is added to the patient record (`PatientRestriction`)
   and the relevant clinical and billing screens display it.
3. We notify the patient if we cannot honour the restriction
   (and we explain why).
4. The patient may terminate the restriction at any time, in
   writing or orally with documentation.

## 5. Right to confidential communications (§ 164.522(b))

A patient may request that we communicate with them in a particular
way (e.g. only by mail, only at work) or at a particular location.
We must accommodate **reasonable** requests; we may require the
request in writing and may condition the request on a method of
payment (when the request is to a non-default address).

The patient's contact preferences are stored on the patient record
and respected by the appointment-reminder, billing, and lab-result
notification flows.

## 6. Right to receive a notice (§ 164.520)

A patient may receive a paper copy of the Notice of Privacy
Practices (`docs/NOTICE_OF_PRIVACY_PRACTICES.md`) on request, even
if they have already agreed to receive it electronically. Front
desk hands one over and records the second receipt.

## 7. Right to file a complaint (§ 164.530(d))

The Privacy Officer accepts complaints in any form (in person,
phone, email, portal) and acknowledges them within 5 business
days. The complaint is investigated and a written response is
provided within 30 days. The patient is also told they may file a
complaint with HHS OCR.

**Retaliation** against a patient who files a complaint is
expressly forbidden by § 164.530(g) and by this entity's policy;
any retaliation is a Category D violation under
`docs/SANCTIONS_POLICY.md`.

## 8. Records and retention

Patient-rights request records are retained for **six years** from
disposition (§ 164.530(j)). The register includes:

- Tracking number, date opened, date closed.
- Patient name, MRN.
- Right asserted, scope of the request.
- Identity-verification method.
- Disposition (granted, partially granted, denied) and rationale.
- Communications with the patient.
- The disclosed records, where applicable, in their archived form.

The register is itself PHI and lives in the secure document store
under the same retention and access controls as the medical record.
