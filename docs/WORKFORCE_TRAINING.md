# Workforce Training & Awareness Program

**Regulatory basis:** 45 CFR § 164.308(a)(5) (Security Awareness and
Training) — the covered entity must implement a security awareness
and training program for **all** members of its workforce, including
management, contractors, and trainees.

This document is the syllabus, cadence, and recordkeeping standard
for the program. The training material itself is delivered through
{lms_or_in_person_method}; this document tells you **what** must be
covered and **how often**.

---

## 1. Cadence

| Trigger | Required training | Within |
|---------|-------------------|--------|
| Hire / on-boarding | Initial training (full syllabus, §3) | 5 business days **before** any access to PHI |
| Annual refresh | Refresh training (covers updates + the previous year's incidents) | The anniversary month of hire ± 30 days |
| Role change with broader access | Targeted training on the new role's specific duties | 5 business days of effective date |
| Material policy change | Awareness module on the change | 30 days of policy effective date |
| After a sanctionable incident | Targeted remediation module | 14 days of disposition (`docs/SANCTIONS_POLICY.md`) |
| Phishing test failure | Anti-phishing micro-module | 7 days |

A workforce member whose training is overdue by more than 30 days has
their MedPharm account flagged as **non-compliant**. The
account remains active (so patient care is not interrupted) but the
overdue training is logged daily until the workforce member
completes it. Two consecutive monthly overdue notices escalate to
the supervisor.

## 2. Roles & responsibilities

| Role | Responsibility |
|------|----------------|
| Privacy Officer | Owns the syllabus; signs off on annual updates. |
| Security Officer | Owns the technical-controls module; reviews incident-driven content. |
| HR / Training Coordinator | Schedules sessions; tracks attendance; maintains the training register. |
| Supervisor | Confirms direct reports complete training on time; escalates overdue cases. |
| Workforce Member | Completes assigned training by the deadline; reports anything that doesn't make sense. |

## 3. Initial training syllabus

### 3.1 What HIPAA requires of you (60 min)

- The HIPAA Privacy, Security, and Breach Notification Rules — what
  each covers, in plain English.
- Definition of PHI, ePHI, and the "minimum necessary" standard.
- Permitted uses and disclosures (treatment, payment, operations).
- Patient rights and how to route a request (access, amendment,
  accounting, restriction, confidential communications,
  complaints) — pointer to `docs/PATIENT_RIGHTS.md`.
- Notice of Privacy Practices — what we tell patients
  (`docs/NOTICE_OF_PRIVACY_PRACTICES.md`).
- Sanctions for non-compliance (`docs/SANCTIONS_POLICY.md`).

### 3.2 The MedPharm controls you use every day (60 min)

- **Logging in** — strong password rules; how to enrol MFA; account
  lockout; idle timeout and session expiry.
- **Choosing your role** — RBAC and "minimum necessary"; why a nurse
  cannot prescribe and a doctor cannot edit billing without a
  separate override.
- **Reading PHI** — every read is logged in `phi_access_log`; the
  audit chain is tamper-evident; pretend you are being watched
  because the system is.
- **Writing PHI** — what a normal vs. an emergency-mode entry looks
  like; why "Emergency mode" must be explicitly invoked
  (`docs/CONTINGENCY_PLAN.md`).
- **Sending PHI** — secure messaging via the patient portal is
  preferred; standard email is **not** for PHI; faxes go to the
  audited e-fax service only; SMS is **never** acceptable for PHI.
- **Mobile devices** — only enrolled, encrypted, locked devices may
  carry the mobile clients; lost or stolen devices are reported to
  the Security Officer the same day.
- **Working from home** — workstation must be encrypted, screen
  must lock automatically, family members must not see the screen.
  Public Wi-Fi requires the VPN.
- **Printing** — pull-to-print queue; nothing left at the printer
  overnight.
- **Disposal** — paper containing PHI goes to the locked shred bin;
  electronic PHI on retired devices is wiped or destroyed per the
  data-retention policy (`docs/DATA_RETENTION_POLICY.md`).

### 3.3 Recognising threats (45 min)

- Phishing — including spear-phishing of clinicians.
- Pretexting — the social-engineering attack on the front desk.
- Tailgating into a secure area.
- Removable media — why USB drives are forbidden.
- Shoulder-surfing — at the front desk, in the cafe.
- Ransomware — what it looks like, what to do, what *not* to do.
- Public Wi-Fi and travel risks.

### 3.4 What to do when something goes wrong (30 min)

- Hit the duress button (Privacy Officer) — there is no penalty for
  raising the alarm.
- Preserve, don't fix — leave the scene undisturbed where possible
  so the audit trail is intact.
- Where to find this document, the breach-notification playbook,
  and the contingency plan.
- Whistleblower protections.

## 4. Annual refresh syllabus

The annual refresh is shorter (typically 60 min) and re-uses the
initial syllabus modules **plus**:

- A summary of the previous year's incidents (de-identified) and the
  lessons learned.
- Any change to the policies, controls, or vendor stack.
- A walk-through of one new attack pattern observed in the wider
  health-care industry that year.

## 5. Role-specific modules

Beyond the common syllabus, role-specific modules are required for:

- **Front desk / Receptionist** — verifying patient identity,
  handling walk-ins, recording emergency-mode access, the PHI
  release form.
- **Clinicians (Doctor / Nurse / Pharmacist)** — minimum-necessary
  in the chart, the prescribing workflow including drug-interaction
  checks, when to use emergency-access break-glass.
- **Administrators** — RBAC management, account lifecycle (provision,
  modify, terminate), audit-log queries, MFA reset.
- **Developers and IT** — secure coding, the "no PHI in logs"
  rule, the vendor-management process for any new integration.

## 6. Recordkeeping

For every training event the Training Coordinator records:

| Field | Source |
|-------|--------|
| Date | LMS / sign-in sheet |
| Trainer | Schedule |
| Topic | Syllabus reference (e.g. §3.1) |
| Workforce member name | Sign-in sheet / LMS account |
| Workforce member role | HR system |
| Result | Pass / fail / make-up scheduled |

Training records are retained for **six years** (§ 164.530(j)).

## 7. Effectiveness

The program is reviewed annually by the Privacy Officer. The review
considers:

- Coverage rate (% of the workforce trained on time).
- Phishing-test results (clicked / reported / no action).
- Incident rate, by category, vs. the previous year.
- Free-text feedback from the post-training survey.
- Updates to the regulatory or threat landscape.

A material drop in any of these is a finding that feeds the next
year's risk analysis and risk-management plan.
