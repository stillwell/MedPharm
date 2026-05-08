# Workforce Sanctions Policy

**Regulatory basis:** 45 CFR § 164.308(a)(1)(ii)(C) (Sanctions
Policy). The covered entity must apply appropriate sanctions against
workforce members who fail to comply with the security policies and
procedures.

This policy is binding on every workforce member of
{covered_entity_name} — employees, contractors, students, interns,
and volunteers — who has any access to MedPharm or to PHI in any
form.

---

## 1. Principles

- Sanctions are **proportionate** to the violation and the harm
  caused.
- Sanctions apply equally regardless of the workforce member's
  seniority.
- Sanctions are documented, tracked, and retained for **six years**
  (§ 164.530(j)).
- Reporting a violation in good faith is **never** sanctionable.
  Retaliation against a good-faith reporter is a separate, severe
  violation of this policy.

## 2. Categories of violation

### Category A — Inadvertent or low-risk

Examples: leaving a workstation unlocked while away from the desk;
walking out of the office with a chart and returning it the same
day; using a personal phone for a brief, otherwise-permitted
treatment communication.

**Standard sanction.** Verbal counselling by the supervisor; the
incident is logged in the workforce member's training file. Up to
two Category A incidents in a 12-month period; the third is treated
as Category B.

### Category B — Negligent or significant

Examples: misdirected fax / email containing PHI; loss of an
unencrypted device; weak or shared password; failure to log out;
emailing PHI to a personal address; ignoring a known security alert
("phishing test failed twice").

**Standard sanction.** Written warning; mandatory targeted training
within 14 days; the incident is logged in the personnel file. A
second Category B incident in 24 months is treated as Category C.

### Category C — Wilful or pattern

Examples: snooping on a record without a treatment, payment, or
operations basis; sharing credentials; circumventing a security
control deliberately; using an emergency-access break-glass without
the required justification; copying PHI to an unauthorised system
or device.

**Standard sanction.** Final written warning; suspension without
pay for one to ten working days; mandatory training; reassignment
of duties if appropriate. **Termination is on the table** if any
aggravating factor is present (large patient count; sensitive
categories such as mental health, substance use, HIV/STI; patient
harm; involvement of a celebrity / public-figure record).

### Category D — Malicious or criminal

Examples: deliberate disclosure of PHI for personal gain or to
harm a patient; attempted sale of PHI; deliberate destruction or
falsification of records; impersonation of another workforce
member; tampering with the audit log.

**Standard sanction.** **Immediate termination** for cause.
Referral to law enforcement and to applicable licensing boards.
Civil and criminal remedies are pursued at the discretion of
counsel. Cyber-liability carrier is notified.

## 3. Procedure

1. **Discovery.** Any workforce member, patient, or vendor who
   suspects a violation reports to the Privacy Officer or Security
   Officer. Reports may be anonymous; the entity's whistleblower
   policy applies.
2. **Triage.** The Privacy Officer or Security Officer opens an
   incident record within one business day. The incident is given
   a tracking number used for all subsequent documents.
3. **Investigation.** Audit-log queries, interviews, and any
   other relevant evidence are collected. The investigator must be
   independent of the workforce member under investigation. The
   audit chain is preserved (no destructive operations against
   `audit_log` or `phi_access_log`).
4. **Determination.** The Privacy Officer (or, in their absence,
   the senior officer of the entity) determines the category of
   the violation in writing.
5. **Hearing.** The workforce member has the opportunity to be
   heard, in person or in writing, **before** Category C or D
   sanctions are imposed (Category A and B may be acted on
   immediately and contested afterwards).
6. **Action.** The sanction is communicated in writing; a copy
   goes into the personnel file and the incident record.
7. **Notification.** If the violation involved a breach of
   unsecured PHI, the breach-notification workflow in
   `docs/BREACH_NOTIFICATION.md` runs in parallel.
8. **Closure.** The incident is closed only when the sanction has
   been carried out, any required training has been completed, and
   the post-mortem has been recorded.

## 4. Mitigating and aggravating factors

When determining a sanction, the following are considered:

**Mitigating** — voluntary self-reporting; quick remediation; no
patient harm; cooperation with the investigation; first incident; a
demonstrably reasonable misunderstanding of policy.

**Aggravating** — concealment; pattern of similar violations; harm
to patients; large number of records; sensitive PHI categories;
seniority of the workforce member (greater duty of care); profit
motive; refusal to participate in remediation.

## 5. Records and retention

The Privacy Officer maintains a sanctions register containing, for
every closed incident:

- Tracking number, date opened, date closed.
- Category determined.
- Workforce member's name, role, and supervisor.
- Sanction applied.
- Whether a breach-notification workflow ran.
- Cross-reference to any audit-log forensic export.

The register is retained for **six years** from the date of
disposition (§ 164.530(j)).

## 6. Acknowledgement

Every workforce member signs the following statement on hire and at
each annual training refresh:

> I have read the {covered_entity_name} Workforce Sanctions Policy,
> I understand it, and I understand that violations will be subject
> to the sanctions described in it. I understand that good-faith
> reporting of violations is encouraged and protected.
>
> Signature ____________________  Date ________
